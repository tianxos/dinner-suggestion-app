from __future__ import annotations

import json
import os
from datetime import datetime

import streamlit as st
from supabase import create_client, Client

_supabase: Client | None = None


def _get_client() -> Client:
    global _supabase
    if _supabase is None:
        url = ""
        key = ""
        try:
            url = st.secrets["SUPABASE_URL"]
            key = st.secrets["SUPABASE_KEY"]
        except Exception:
            url = os.environ.get("SUPABASE_URL", "")
            key = os.environ.get("SUPABASE_KEY", "")
        if not url or not key:
            raise RuntimeError(
                "Set SUPABASE_URL and SUPABASE_KEY in Streamlit secrets "
                "(or .env for local dev)."
            )
        _supabase = create_client(url, key)
    return _supabase


def init_db() -> None:
    client = _get_client()
    # Tables are created in Supabase SQL Editor; this is a no-op placeholder
    # so the rest of the app can still call init_db() without error.
    pass


# ── Recipes (history) ───────────────────────────────────────────────────────

def save_recipe(name: str, why: str, steps: list[str],
                ingredients_used: str, time_limit: str, diet: str,
                nutrition: str | None = None,
                language: str = "en",
                recipe_ingredients: list[str] | None = None) -> int:
    client = _get_client()
    data = {
        "name": name,
        "why": why,
        "steps": json.dumps(steps),
        "ingredients_used": ingredients_used,
        "recipe_ingredients": json.dumps(recipe_ingredients) if recipe_ingredients else None,
        "time_limit": time_limit,
        "diet": diet,
        "nutrition": nutrition,
        "language": language,
    }
    result = client.table("recipes").insert(data).execute()
    return result.data[0]["id"]


def get_history(limit: int = 50, favorites_only: bool = False) -> list[dict]:
    client = _get_client()
    query = client.table("recipes").select("*").order("created_at", desc=True).limit(limit)
    if favorites_only:
        query = query.eq("is_favorite", True)
    rows = query.execute().data
    result = []
    for r in rows:
        r["steps"] = json.loads(r["steps"]) if isinstance(r["steps"], str) else r["steps"]
        result.append(r)
    return result


def toggle_favorite(recipe_id: int) -> None:
    client = _get_client()
    row = client.table("recipes").select("is_favorite").eq("id", recipe_id).execute().data
    if row:
        new_val = 0 if row[0]["is_favorite"] else 1
        client.table("recipes").update({"is_favorite": new_val}).eq("id", recipe_id).execute()


def set_rating(recipe_id: int, rating: int) -> None:
    client = _get_client()
    client.table("recipes").update({"rating": rating}).eq("id", recipe_id).execute()


def delete_recipe(recipe_id: int) -> None:
    client = _get_client()
    client.table("recipes").delete().eq("id", recipe_id).execute()


def clear_history() -> None:
    client = _get_client()
    client.table("recipes").delete().neq("id", 0).execute()


# ── Saved dishes ────────────────────────────────────────────────────────────

def save_dish(name: str, ingredients: list[str], steps: list[str],
              notes: str = "", dietary_tags: list[str] | None = None) -> None:
    client = _get_client()
    data = {
        "name": name,
        "ingredients": json.dumps(ingredients),
        "steps": json.dumps(steps),
        "notes": notes,
        "dietary_tags": json.dumps(dietary_tags) if dietary_tags else None,
    }
    client.table("saved_dishes").insert(data).execute()


def get_saved_dishes() -> list[dict]:
    client = _get_client()
    rows = client.table("saved_dishes").select("*").order("created_at", desc=True).execute().data
    return [_parse_dish(r) for r in rows]


def get_dish_by_id(dish_id: int) -> dict | None:
    client = _get_client()
    row = client.table("saved_dishes").select("*").eq("id", dish_id).execute().data
    return _parse_dish(row[0]) if row else None


def search_dishes_by_ingredients(user_ings: list[str]) -> list[tuple[dict, int]]:
    """Return dishes sorted by how many of the user's ingredients they match."""
    dishes = get_saved_dishes()
    scored = []
    for d in dishes:
        dish_ings = [i.lower() for i in d.get("ingredients", [])]
        matches = sum(1 for u in user_ings
                      if any(u.lower() in di or di in u.lower() for di in dish_ings))
        if matches > 0:
            scored.append((d, matches))
    scored.sort(key=lambda x: -x[1])
    return scored


def set_dish_rating(dish_id: int, rating: int) -> None:
    client = _get_client()
    client.table("saved_dishes").update({"rating": rating}).eq("id", dish_id).execute()


def delete_dish(dish_id: int) -> None:
    client = _get_client()
    client.table("saved_dishes").delete().eq("id", dish_id).execute()


def _parse_dish(row) -> dict:
    d = dict(row)
    d["ingredients"] = json.loads(d["ingredients"]) if isinstance(d.get("ingredients"), str) else d.get("ingredients", [])
    d["steps"] = json.loads(d["steps"]) if isinstance(d.get("steps"), str) else d.get("steps", [])
    tags = d.get("dietary_tags")
    d["dietary_tags"] = json.loads(tags) if isinstance(tags, str) else (tags or [])
    return d


# ── Preferences ─────────────────────────────────────────────────────────────

def get_pref(key: str, default: str | None = None) -> str | None:
    client = _get_client()
    row = client.table("preferences").select("value").eq("key", key).execute().data
    return row[0]["value"] if row else default


def set_pref(key: str, value: str) -> None:
    client = _get_client()
    client.table("preferences").upsert({"key": key, "value": value}).execute()


def get_taste_profile() -> tuple[list[dict], list[dict]]:
    client = _get_client()
    liked = client.table("recipes").select("name, why").eq("rating", 1).order("created_at", desc=True).limit(5).execute().data
    disliked = client.table("recipes").select("name").eq("rating", -1).order("created_at", desc=True).limit(5).execute().data
    return liked, disliked
