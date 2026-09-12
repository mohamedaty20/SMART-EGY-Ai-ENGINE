"""
services/ai_service.py — Thin wrapper around google-genai.
"""
import asyncio
from google.genai import types
from config import client, GEMINI_MODEL


async def call_gemini_json(contents, temperature=0.0, timeout=45):
    """
    Call Gemini and return raw text. Default timeout 45 seconds.
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

    print("[ai] calling model=" + str(GEMINI_MODEL) + " timeout=" + str(timeout))
    try:
        response = await asyncio.wait_for(_one_call(), timeout=timeout)
        txt = response.text or ""
        print("[ai] response length=" + str(len(txt)))
        return txt
    except asyncio.TimeoutError:
        print("[ai] TIMEOUT after " + str(timeout) + "s")
        raise Exception("AI request timed out after " + str(timeout) + "s.")
    except Exception as e:
        print("[ai] FAILED: " + repr(e))
        raise Exception("AI request failed: " + str(e))
