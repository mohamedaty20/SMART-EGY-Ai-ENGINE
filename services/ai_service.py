"""
services/ai_service.py

Thin wrapper around google-genai. One function for JSON responses.
"""
import asyncio
from google.genai import types
from config import client, GEMINI_MODEL


async def call_gemini_json(contents, temperature=0.0, timeout=180):
    """
    Call Gemini and return raw text. Raises on failure.
    'contents' can be a string or a list of strings and Part objects.
    """
    if not client:
        raise Exception("GEMINI_API_KEY missing.")

    config = types.GenerateContentConfig(temperature=temperature)

    async def _one_call():
        return await client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=contents,
            config=config,
        )

    try:
        response = await asyncio.wait_for(_one_call(), timeout=timeout)
        return response.text or ""
    except asyncio.TimeoutError:
        raise Exception(f"AI request timed out after {timeout}s.")
    except Exception as e:
        raise Exception(f"AI request failed: {e}")
