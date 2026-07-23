import os
import json
from groq import Groq, AuthenticationError, APIError
from config import GROQ_MODEL, GROQ_API_KEY


def get_api_key() -> str:
    """Read API key dynamically from env in case .env was updated."""
    from dotenv import load_dotenv
    load_dotenv(override=True)
    key = os.getenv("GROQ_API_KEY", "").strip().strip('"').strip("'")
    if not key or key == "your_groq_api_key_here":
        raise ValueError("Groq API Key is missing or invalid in .env file. Please set GROQ_API_KEY=gsk_... in .env")
    return key


def get_client() -> Groq:
    api_key = get_api_key()
    return Groq(api_key=api_key)


def chat_complete(system_prompt: str, user_message: str) -> str:
    """Non-streaming completion — returns full text response."""
    try:
        client = get_client()
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()
    except AuthenticationError:
        raise ValueError("Invalid Groq API Key (401 Unauthorized). Please check GROQ_API_KEY in your .env file.")
    except APIError as e:
        raise RuntimeError(f"Groq API Error: {str(e)}")


def chat_stream(system_prompt: str, messages: list):
    """
    Streaming generator — yields text chunks.
    `messages` is a list of {"role": ..., "content": ...} dicts.
    """
    try:
        client = get_client()
        stream = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            temperature=0.7,
            max_tokens=1024,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except AuthenticationError:
        raise ValueError("Invalid Groq API Key (401 Unauthorized). Please check GROQ_API_KEY in your .env file.")
    except APIError as e:
        raise RuntimeError(f"Groq API Error: {str(e)}")


def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    with open(f"prompts/{name}.txt", "r", encoding="utf-8") as f:
        return f.read()
