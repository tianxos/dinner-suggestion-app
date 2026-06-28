from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import hashlib
import json
import os
import random
import re
import time

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

from models import Recipe, RecipeSuggestions
from prompts import build_prompt

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
ZEN_API_KEY = os.getenv("ZEN_API_KEY", "")
ZEN_MODEL = os.getenv("ZEN_MODEL", "mimo-v2.5-free")
ZEN_BASE_URL = "https://opencode.ai/zen/v1"

# ── In-memory cache ─────────────────────────────────────────────────────────
_CACHE_TTL = 3600  # 1 hour
_cache: dict[str, tuple[float, list[Recipe]]] = {}


def _cache_key(ingredients: str, time_limit: str, diet: str, language: str) -> str:
    raw = f"{ingredients}|{time_limit}|{diet}|{language}"
    return hashlib.md5(raw.encode()).hexdigest()


def use_zen() -> bool:
    return bool(ZEN_API_KEY)


def get_client() -> genai.Client:
    if use_zen():
        raise RuntimeError("Use get_zen_client() when ZEN_API_KEY is set.")
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No API key found. Set GEMINI_API_KEY or ZEN_API_KEY in a .env file "
            "(see .env.example) and restart the app."
        )
    return genai.Client(api_key=api_key)


def get_zen_client():
    from openai import OpenAI
    return OpenAI(api_key=ZEN_API_KEY, base_url=ZEN_BASE_URL)


def _extract_json(text: str) -> dict:
    """Extract JSON from model response, handling markdown code fences."""
    text = text.strip()
    m = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if m:
        text = m.group(1).strip()
    return json.loads(text)


def _parse_recipes_from_text(text: str) -> list[Recipe]:
    """Parse recipes from free-form model text."""
    data = _extract_json(text)
    if isinstance(data, dict) and "recipes" in data:
        return [Recipe(**r) for r in data["recipes"]]
    if isinstance(data, list):
        return [Recipe(**r) for r in data]
    raise ValueError(f"Unexpected JSON structure: {type(data)}")


def generate_recipes(
    ingredients: str,
    time_limit: str,
    diet: str,
    language: str = "en",
    saved_dishes: list[dict] | None = None,
    taste_traits: str | None = None,
) -> list[Recipe]:
    if use_zen():
        return _generate_recipes_zen(ingredients, time_limit, diet, language, saved_dishes, taste_traits)
    return _generate_recipes_gemini(ingredients, time_limit, diet, language, saved_dishes, taste_traits)


def _generate_recipes_zen(
    ingredients: str,
    time_limit: str,
    diet: str,
    language: str,
    saved_dishes: list[dict] | None,
    taste_traits: str | None,
) -> list[Recipe]:
    use_cache = not saved_dishes and not taste_traits
    if use_cache:
        ckey = _cache_key(ingredients, time_limit, diet, language)
        if ckey in _cache:
            ts, cached = _cache[ckey]
            if time.time() - ts < _CACHE_TTL:
                return cached

    client = get_zen_client()
    nonce = random.randint(1, 1_000_000)
    prompt = build_prompt(ingredients, time_limit, diet, language, nonce, saved_dishes, taste_traits)
    prompt += (
        "\n\nYou MUST respond with valid JSON only, no markdown. "
        "Return: {\"recipes\": [{\"name\": \"...\", \"why\": \"...\", "
        "\"ingredients\": [\"...\"], \"steps\": [\"...\"], \"nutrition\": \"...\"}]}"
    )

    last_exc: Exception | None = None
    for attempt in range(2):
        try:
            resp = client.chat.completions.create(
                model=ZEN_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
            )
            text = resp.choices[0].message.content or ""
            recipes = _parse_recipes_from_text(text)[:2]
            for r in recipes:
                r.steps = r.steps[:6]

            if use_cache:
                _cache[ckey] = (time.time(), recipes)
            return recipes

        except Exception as exc:
            last_exc = exc
            msg = str(exc).lower()
            if any(w in msg for w in ("rate", "timeout", "unavailable", "503", "429")):
                time.sleep(1.5 * (attempt + 1))
                continue
            raise

    raise last_exc  # type: ignore[misc]


def _generate_recipes_gemini(
    ingredients: str,
    time_limit: str,
    diet: str,
    language: str,
    saved_dishes: list[dict] | None,
    taste_traits: str | None,
) -> list[Recipe]:
    use_cache = not saved_dishes and not taste_traits
    if use_cache:
        ckey = _cache_key(ingredients, time_limit, diet, language)
        if ckey in _cache:
            ts, cached = _cache[ckey]
            if time.time() - ts < _CACHE_TTL:
                return cached

    client = get_client()
    nonce = random.randint(1, 1_000_000)
    prompt = build_prompt(ingredients, time_limit, diet, language, nonce, saved_dishes, taste_traits)

    last_exc: Exception | None = None
    for attempt in range(2):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=RecipeSuggestions,
                    temperature=0.9,
                ),
            )
            data = RecipeSuggestions.model_validate_json(response.text)
            recipes = data.recipes[:2]
            for r in recipes:
                r.steps = r.steps[:6]

            if use_cache:
                _cache[ckey] = (time.time(), recipes)
            return recipes

        except genai_errors.APIError as exc:
            last_exc = exc
            msg = str(exc).lower()
            if any(w in msg for w in ("rate", "timeout", "unavailable", "503", "429")):
                time.sleep(1.5 * (attempt + 1))
                continue
            raise

    raise last_exc  # type: ignore[misc]
