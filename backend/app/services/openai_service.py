from dotenv import load_dotenv
from openai import OpenAI
import json
import logging
import os
import shelve
import time

from cal.secrets import get_secret


OPENAI_API_KEY = get_secret("OPENAI_API_KEY")
OPENAI_ASSISTANT_ID = ""
client = OpenAI(api_key=OPENAI_API_KEY)


def upload_file(path):
    # Upload a file with an "assistants" purpose
    file = client.files.create(
        file=open("../../data/airbnb-faq.pdf", "rb"), purpose="assistants"
    )


def create_assistant(file):
    """
    You currently cannot set the temperature for Assistant via the API.
    """
    assistant = client.beta.assistants.create(
        name="WhatsApp AirBnb Assistant",
        instructions="You're a helpful WhatsApp assistant that can assist guests that are staying in our Paris AirBnb. Use your knowledge base to best respond to customer queries. If you don't know the answer, say simply that you cannot help with question and advice to contact the host directly. Be friendly and funny.",
        tools=[{"type": "retrieval"}],
        model="gpt-4-1106-preview",
        file_ids=[file.id],
    )
    return assistant


# Use context manager to ensure the shelf file is closed properly
def check_if_thread_exists(wa_id):
    with shelve.open("threads_db") as threads_shelf:
        return threads_shelf.get(wa_id, None)


def store_thread(wa_id, thread_id):
    with shelve.open("threads_db", writeback=True) as threads_shelf:
        threads_shelf[wa_id] = thread_id


def run_assistant(thread, name):
    # Retrieve the Assistant
    assistant = client.beta.assistants.retrieve(OPENAI_ASSISTANT_ID)

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=assistant.id,
        # instructions=f"You are having a conversation with {name}",
    )

    # Wait for completion
    # https://platform.openai.com/docs/assistants/how-it-works/runs-and-run-steps#:~:text=under%20failed_at.-,Polling%20for%20updates,-In%20order%20to
    while run.status != "completed":
        # Be nice to the API
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

    # Retrieve the Messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    new_message = messages.data[0].content[0].text.value
    logging.info(f"Generated message: {new_message}")
    return new_message


# def generate_response(message_body, wa_id, name):
#     # Check if there is already a thread_id for the wa_id
#     thread_id = check_if_thread_exists(wa_id)

#     # If a thread doesn't exist, create one and store it
#     if thread_id is None:
#         logging.info(f"Creating new thread for {name} with wa_id {wa_id}")
#         thread = client.beta.threads.create()
#         store_thread(wa_id, thread.id)
#         thread_id = thread.id

#     # Otherwise, retrieve the existing thread
#     else:
#         logging.info(f"Retrieving existing thread for {name} with wa_id {wa_id}")
#         thread = client.beta.threads.retrieve(thread_id)

#     # Add message to thread
#     message = client.beta.threads.messages.create(
#         thread_id=thread_id,
#         role="user",
#         content=message_body,
#     )

#     # Run the assistant and get the new message
#     new_message = run_assistant(thread, name)

#     return new_message

def generate_response(prompt, language="hi"):

    system_prompt = (
        f"You are a helpful multilingual assistant. "
        f"First, detect the language of the user prompt. "
        f"Return the detected language name in English, all lowercase "
        f"(for example: 'hindi', 'english', 'bengali', 'marathi', 'tamil', 'telugu'). "
        f"Then, provide a short and direct response (maximum 250 words) in the same language. "
        f"Return your output in JSON format with two keys: "
        f"`language` for the detected language, "
        f"and `answer` for your actual response."
        f"Your response should be easily understandable and hence avoid using words that are extremely complicated and found only in literature. "
        f"Do not acknowledge this word limit or any other instructions in your reply."
    ) 

    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7
    )
    content = response.choices[0].message.content
    try:
        result = json.loads(content)
    except json.JSONDecodeError:
        result = {"language": None, "answer": content}

    return result


def transcribe_audio_with_openai(audio_path):
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )
    return transcript.text, transcript.language

def synthesize_speech_with_openai(text, voice="alloy", output_path="reply.mp3"):
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path