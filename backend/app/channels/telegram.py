from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import logging
import os
import requests
import uuid
from typing import Dict, Any, Optional, List

from app.services.openai_service import (
    generate_response,
    transcribe_audio_with_openai,
    synthesize_speech_with_openai
)
from app.services.google_service import synthesize_speech_with_google
from cal.storage import upload_to_gcs
from cal.firestore import (
    get_weekly_stats,
    set_weekly_stats,
    get_overall_summary,
    set_overall_summary,
    log_interaction,
    Increment
)

LANGUAGE_MAP = {
    "hindi":      {"google_code": "hi-IN"},
    "bengali":    {"google_code": "bn-IN"},
    "marathi":    {"google_code": "mr-IN"},
    "tamil":      {"google_code": "ta-IN"},
    "telugu":     {"google_code": "te-IN"},
    "gujarati":   {"google_code": "gu-IN"},
    "kannada":    {"google_code": "kn-IN"},
    "malayalam":  {"google_code": "ml-IN"},
    "punjabi":    {"google_code": "pa-IN"},
    "urdu":       {"google_code": "ur-IN"},
    "english":    {"google_code": "en-IN"},
    "spanish":    {"google_code": "es-ES", "voice": "es-ES-Standard-G"},
    "french":     {"google_code": "fr-FR", "voice": "fr-FR-Standard-G"},
    "german":     {"google_code": "de-DE", "voice": "de-DE-Standard-H"},
    "portuguese": {"google_code": "pt-PT", "voice": "pt-BR-Standard-B"},
    "russian":    {"google_code": "ru-RU", "voice": "ru-RU-Standard-B"},
    "japanese":   {"google_code": "ja-JP", "voice": "ja-JP-Standard-C"},
    "chinese":    {"google_code": "zh-CN", "voice": "cmn-CN-Standard-B"},
    "arabic":     {"google_code": "ar-XA"},
}

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/"

# -----------------------------
# 📅 DATE UTILITY
# -----------------------------
def get_week_start_date_str(date: Optional[datetime] = None) -> str:
    """Calculates the date string (YYYYMMDD) for the most recent Monday."""
    if date is None:
        date = datetime.now()
    days_since_monday = date.weekday()
    monday_date = date - timedelta(days=days_since_monday)
    return monday_date.strftime("%Y%m%d")

def generate_log_doc_id(user_id: str, timestamp: datetime) -> str:
    """Generates the custom log document ID: <YYYMMDD><HHMMSS>_<user_id>"""
    time_str = timestamp.strftime("%Y%m%d%H%M%S")
    return f"{time_str}_{user_id}"

# -----------------------------
# 🤖 APPLICATION LOGIC FOR UPDATES
# -----------------------------
def update_language_distribution(current_data: Dict[str, Any], lang: str, is_voice: bool) -> Dict[str, Any]:
    """
    Updates the language_distribution array in a document (overall or weekly).
    Performs a Read-Modify-Write operation on the array.
    """
    
    lang_dist: List[Dict] = current_data.get("language_distribution", [])
    
    # Find existing language entry
    found = False
    for item in lang_dist:
        if item.get("lang") == lang:
            item["interactions"] = item.get("interactions", 0) + 1
            if is_voice:
                item["voice"] = item.get("voice", 0) + 1
            found = True
            break
            
    # If language not found, create a new entry
    if not found:
        new_entry = {
            "lang": lang,
            "interactions": 1,
            "voice": 1 if is_voice else 0
        }
        lang_dist.append(new_entry)

    current_data["language_distribution"] = lang_dist
    return current_data


def handle_new_interaction(interaction_data: Dict[str, Any], is_new_user: bool = False, timestamp: Optional[datetime] = None):
    """
    Primary function to update all Firestore documents after a single interaction.

    Args:
        interaction_data: A dict containing log data (must include 'user_id', 'lang', 'modal').
        is_new_user: Boolean indicating if this is the first interaction for this user_id.
        timestamp: Optional datetime object representing the interaction timestamp.
    """
    logging.info("handle_new_interaction called")
    # -----------------------------
    # PREPARE DATA
    # -----------------------------
    user_id = interaction_data['user_id']
    lang = interaction_data['lang']
    modal = interaction_data['modal']
    is_voice = (modal == 'audio')
    
    # Use passed timestamp or generate new if not provided
    log_entry_data = interaction_data.copy()
    log_entry_data["date"] = timestamp if timestamp else datetime.now(ZoneInfo("Asia/Kolkata"))
    
    # -----------------------------
    # 1. LOG THE INTERACTION (Custom ID)
    # -----------------------------
    log_interaction(log_entry_data)
    
    # -----------------------------
    # 2. UPDATE WEEKLY STATS (Read-Modify-Write)
    # -----------------------------
    week_id = get_week_start_date_str()
    weekly_stats = get_weekly_stats(week_id) # Read
    
    # Update simple number fields using Increment
    weekly_updates = {
        'interactions': Increment(1),  # changed from "interaction_volume"
        'voice': Increment(1) if is_voice else Increment(0),
        'week_start_date': week_id 
    }
    
    # Update language distribution array
    updated_weekly_stats = update_language_distribution(weekly_stats, lang, is_voice)
    weekly_updates['language_distribution'] = updated_weekly_stats['language_distribution']
    
    set_weekly_stats(week_id, weekly_updates, merge=True) # Write
    
    # -----------------------------
    # 3. UPDATE OVERALL SUMMARY (Read-Modify-Write)
    # -----------------------------
    overall_summary = get_overall_summary() # Read
    
    # Update simple number fields using Increment
    overall_updates = {
        'interactions': Increment(1),         # changed from 'total_interactions'
        'voice': Increment(1) if is_voice else Increment(0),  # changed from 'voice_interactions'
    }

    if is_new_user:
        overall_updates['active_users'] = Increment(1)
        
    # Update language distribution array
    updated_overall_summary = update_language_distribution(overall_summary, lang, is_voice)
    overall_updates['language_distribution'] = updated_overall_summary['language_distribution']
    
    set_overall_summary(overall_updates, merge=True) # Write

    print(f"Firestore updates complete for user {user_id}.")

def get_google_language_code(openai_language):
    """
    Maps an OpenAI/Whisper language name to a Google Cloud TTS BCP-47 code and voice.
    Logs a warning if the language is not in the map.
    Returns (google_code, voice) where voice may be None or empty string.
    """
    lang_name = openai_language.lower()
    entry = LANGUAGE_MAP.get(lang_name)
    if not entry:
        logging.warning(f"[LANGUAGE_MAP] Language '{openai_language}' not found in LANGUAGE_MAP. Defaulting to 'en-IN'.")
        return None, None
    google_code = entry.get("google_code") or None
    voice_code = entry.get("voice") or None
    return google_code, voice_code

def send_message(token, chat_id, text=None, audio_path=None):
    """
    Sends either a text message or an audio message to the specified chat.
    If text is provided, sends a text message.
    If audio_path is provided, sends an audio file.
    """
    if text:
        url = TELEGRAM_API_URL.format(token=token) + "sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logging.error(f"Failed to send Telegram text message: {e}")
            return None
    elif audio_path:
        url = TELEGRAM_API_URL.format(token=token) + "sendAudio"
        try:
            with open(audio_path, "rb") as audio_file:
                files = {"audio": audio_file}
                data = {"chat_id": chat_id}
                response = requests.post(url, data=data, files=files, timeout=20)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logging.error(f"Failed to send Telegram audio message: {e}")
            return None
    else:
        logging.error("No text or audio_path provided to send_message.")
        return None

def recv_message(update):
    """
    Extracts chat_id and content from the Telegram update.
    Returns a tuple: (chat_id, content_type, content)
    - content_type: 'text' or 'audio'
    - content: text string or audio file_id
    Returns (None, None, None, None) if not a message.
    """
    message = update.get("message")
    if not message:
        return None, None, None, None
    user_id = None
    if "from" in message and "id" in message["from"]:
        user_id = message["from"]["id"]
    chat_id = message["chat"]["id"]
    if "text" in message:
        return chat_id, user_id, "text", message["text"]
    elif "voice" in message:
        # For voice messages, Telegram uses 'voice' field with a file_id
        file_id = message["voice"]["file_id"]
        return chat_id, user_id, "audio", file_id
    else:
        return chat_id, user_id, None, None

def download_telegram_audio(token, file_id, output_path="voice.ogg"):
    # Get file path from Telegram
    url = TELEGRAM_API_URL.format(token=token) + f"getFile?file_id={file_id}"
    resp = requests.get(url)
    resp.raise_for_status()
    file_path = resp.json()["result"]["file_path"]
    # Download the file
    file_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
    audio_resp = requests.get(file_url)
    audio_resp.raise_for_status()
    with open(output_path, "wb") as f:
        f.write(audio_resp.content)
    return output_path

def handle_update(token, update):
    chat_id, user_id, content_type, content = recv_message(update)
    if not chat_id or not content_type:
        return

    # Calculate timestamp once for this interaction (India time)
    timestamp = datetime.now(ZoneInfo("Asia/Kolkata"))

    interaction = {
        "user_id": str(user_id) if user_id else None,
        "question": content,
        "modal": content_type,
        "lang": None,
        "reply": None,
        "audio_file": None,
        "date": timestamp  # Pass timestamp to handle_new_interaction
    }

    if content_type == "text":
        result = generate_response(content)
        reply = result.get("answer")
        language = result.get("language", "english")
        send_message(token, chat_id, text=reply)
        interaction["reply"] = reply
        interaction["lang"] = language

    elif content_type == "audio":
        # Use a unique filename for each audio upload
        audio_filename = f"voice_{user_id}_{timestamp.strftime('%Y%m%d%H%M%S')}.ogg"
        audio_path = download_telegram_audio(token, content, output_path=audio_filename)
        transcript, language = transcribe_audio_with_openai(audio_path)
        result = generate_response(transcript, language=language)
        reply = result.get("answer")
        language = result.get("language", language)
        send_message(token, chat_id, text=reply)
        google_lang_code, google_voice_code = get_google_language_code(language)
        interaction["lang"] = language
        interaction["question"] = transcript
        interaction["reply"] = reply
        interaction["audio_file"] = audio_path
        if google_lang_code is not None:
            unique_audio_path = f"reply_{user_id}_{timestamp.strftime('%Y%m%d%H%M%S')}.mp3"
            audio_reply_path = synthesize_speech_with_google(
                reply, language_code=google_lang_code, voice_code=google_voice_code, output_path=unique_audio_path
            )
            send_message(token, chat_id, audio_path=audio_reply_path)
            os.remove(audio_reply_path)
        gcs_audio_path = upload_to_gcs(audio_path, user_id)
        interaction["audio_file"] = gcs_audio_path

    # Pass timestamp to handle_new_interaction
    handle_new_interaction(interaction, timestamp=timestamp)