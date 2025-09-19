# app/providers.py
import os
import httpx
from typing import List, Dict
from fastapi import HTTPException
import json
from datetime import datetime

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/complete"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# ---- Helper to serialize datetimes ----
def serialize_for_json(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def make_serializable(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def serialize_messages(messages):
    return [
        {k: make_serializable(v) for k, v in m.items()}
        for m in messages
    ]


# ---- OpenAI ----
async def call_openai(model: str, messages: list, temperature: float = 1.0):
    """
    Calls the OpenAI API with given model and messages.
    Ensures all datetime objects are serialized.
    """
    # Make messages JSON serializable
    messages = serialize_messages(messages)

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload,
            headers=headers,
            timeout=30
        )

    if response.status_code != 200:
        raise Exception(f"OpenAI error: {response.text}")

    data = response.json()
    # Return text output
    return data["choices"][0]["message"]["content"]


# ---- Anthropic ----
def to_anthropic_prompt(messages):
    parts = []
    for m in messages:
        role = m["role"]
        content = m["content"]
        if role == "system":
            parts.append(f"\n\nSystem: {content}")
        elif role == "user":
            parts.append(f"\n\nHuman: {content}")
        else:
            parts.append(f"\n\nAssistant: {content}")
    return "".join(parts) + "\n\nAssistant:"

async def call_anthropic(model: str, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=400, detail="Anthropic provider not enabled (ANTHROPIC_API_KEY missing).")
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
    }
    prompt = to_anthropic_prompt(messages)
    payload = {"model": model, "prompt": prompt, "max_tokens_to_sample": 512, "temperature": temperature}
    json_payload = json.dumps(payload, default=serialize_for_json)

    async with httpx.AsyncClient(timeout=60.0) as client:
        r = await client.post(ANTHROPIC_URL, headers=headers, content=json_payload)
        if r.status_code >= 400:
            raise HTTPException(status_code=502, detail=f"Anthropic error: {r.text}")
        data = r.json()
        try:
            return data.get("completion") or ""
        except Exception:
            raise HTTPException(status_code=502, detail=f"Unexpected Anthropic response: {json.dumps(data)[:400]}")

# ---- Unified entrypoint ----
async def call_model(provider: str, model: str, messages: List[Dict[str, str]], temperature: float = 0.7) -> str:
    allow_mock = os.getenv("ALLOW_MOCK", "false").lower() == "true"
    if provider == "openai":
        if os.getenv("OPENAI_API_KEY"):
            return await call_openai(model, messages, temperature)
        if allow_mock:
            return "[MOCK OPENAI reply] This is a mock reply because OPENAI_API_KEY is not set."
        raise HTTPException(status_code=400, detail="OpenAI provider disabled (OPENAI_API_KEY missing).")
    elif provider == "anthropic":
        if os.getenv("ANTHROPIC_API_KEY"):
            return await call_anthropic(model, messages, temperature)
        if allow_mock:
            return "[MOCK ANTHROPIC reply] This is a mock reply because ANTHROPIC_API_KEY is not set."
        raise HTTPException(status_code=400, detail="Anthropic provider disabled (ANTHROPIC_API_KEY missing).")
    else:
        raise HTTPException(status_code=400, detail=f"Unknown provider '{provider}'")

# Points

# call_openai and call_anthropic implement REST calls directly.

#  If ALLOW_MOCK=true, developer can test flows locally without keys (mock replies returned).

# Errors from provider are turned into 502 responses.