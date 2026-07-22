import json
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)


def chat_complete(system_prompt: str, user_message: str) -> str:
    """Non-streaming completion — returns full text response."""
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


def chat_stream(system_prompt: str, messages: list):
    """
    Streaming generator — yields text chunks.
    `messages` is a list of {"role": ..., "content": ...} dicts.
    """
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


def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts/ directory."""
    with open(f"prompts/{name}.txt", "r", encoding="utf-8") as f:
        return f.read()
