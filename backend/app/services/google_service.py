import json
from google.cloud import texttospeech
from google.oauth2 import service_account
from cal.secrets import get_secret

def synthesize_speech_with_google(text, output_path="reply.mp3", language_code="en-IN", voice_name="en-IN-Wavenet-D"):
    creds = get_secret("GOOGLE_APPLICATION_CREDENTIALS")
    if isinstance(creds, str):
        service_account_info = json.loads(creds)
    else:
        service_account_info = creds

    try:
        credentials_object = service_account.Credentials.from_service_account_info(
            service_account_info
        )
    except Exception as e:
        # This catch is helpful for debugging bad JSON structure
        raise ValueError(f"Failed to create Google Credentials object. Check JSON key format: {e}")
    
    client = texttospeech.TextToSpeechClient(credentials=credentials_object)
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name=voice_name or f"{language_code}-Standard-B"
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    with open(output_path, "wb") as out:
        out.write(response.audio_content)
    return output_path