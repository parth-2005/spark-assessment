import os
import json
import re
import asyncio
from typing import Tuple, List
from google import genai
from google.genai import types
from .prompts import SYSTEM_PROMPT
from .provider import get_model_id

_client = None


def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    return _client


def _call_model_sync(query: str):
    client = get_client()
    model_id = get_model_id()
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        tools=[{"google_search": {}}],
        temperature=0.1,
    )

    response = client.models.generate_content(
        model=model_id,
        contents=query,
        config=config,
    )
    return response


async def run_agent(query: str) -> Tuple[dict, List[str]]:
    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(None, _call_model_sync, query)

    # Extract grounding source URLs
    sources = []
    for candidate in getattr(response, "candidates", []):
        meta = getattr(candidate, "grounding_metadata", None)
        if meta:
            for chunk in getattr(meta, "grounding_chunks", []):
                web = getattr(chunk, "web", None)
                if web and getattr(web, "uri", None):
                    sources.append(web.uri)

    # Parse structured JSON — strip markdown fences if present
    text = getattr(response, "text", "")
    text = re.sub(r"```(?:json)?", "", text).strip().strip("`").strip()
    structured = json.loads(text)

    return structured, list(dict.fromkeys(sources))
