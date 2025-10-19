import requests
import logging
import uuid
from app.services.openai_service import (
    generate_response,
    transcribe_audio_with_openai,
    synthesize_speech_with_openai
)
from app.services.google_service import synthesize_speech_with_google
import os

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
    Returns (None, None, None) if not a message.
    """
    message = update.get("message")
    if not message:
        return None, None, None
    chat_id = message["chat"]["id"]
    if "text" in message:
        return chat_id, "text", message["text"]
    elif "voice" in message:
        # For voice messages, Telegram uses 'voice' field with a file_id
        file_id = message["voice"]["file_id"]
        return chat_id, "audio", file_id
    else:
        return chat_id, None, None

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
    chat_id, content_type, content = recv_message(update)
    if not chat_id or not content_type:
        return

    if content_type == "text":
        reply = generate_response(content)
        send_message(token, chat_id, text=reply)
    elif content_type == "audio":
        audio_path = download_telegram_audio(token, content)
        transcript, language = transcribe_audio_with_openai(audio_path)
        reply = generate_response(transcript, language=language)
        send_message(token, chat_id, text=reply)
        google_lang_code, google_voice_code = get_google_language_code(language)
        if google_lang_code is not None:
            unique_audio_path = f"reply_{uuid.uuid4().hex}.mp3"
            audio_reply_path = synthesize_speech_with_google(reply, language_code=google_lang_code, voice_code=google_voice_code, output_path=unique_audio_path)
            send_message(token, chat_id, audio_path=audio_reply_path)
            # Optionally, delete the file after sending to save disk space
            os.remove(audio_reply_path)