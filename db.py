from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dinner_app.db")


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    conn = _conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS recipes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            why         TEXT,
            steps       TEXT,
            ingredients_used TEXT,
            recipe_ingredients TEXT,
            time_limit  TEXT,
            diet        TEXT,
            is_favorite INTEGER DEFAULT 0,
            rating      INTEGER DEFAULT 0,
            nutrition   TEXT,
            language    TEXT DEFAULT 'en',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS saved_dishes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            ingredients TEXT,
            steps       TEXT,
            notes       TEXT DEFAULT '',
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS preferences (
            key   TEXT PRIMARY KEY,
            value TEXT
        );
    """)
    conn.commit()
    # Add columns for schema upgrades
    for col, typ, table in [
        ("recipe_ingredients", "TEXT", "recipes"),
        ("dietary_tags", "TEXT", "saved_dishes"),
        ("rating", "INTEGER DEFAULT 0", "saved_dishes"),
    ]:
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")
            conn.commit()
        except sqlite3.OperationalError:
            pass
    conn.close()


# ── Recipes (history) ───────────────────────────────────────────────────────

def save_recipe(name: str, why: str, steps: list[str],
                ingredients_used: str, time_limit: str, diet: str,
                nutrition: str | None = None,
                language: str = "en",
                recipe_ingredients: list[str] | None = None) -> int:
    conn = _conn()
    cur = conn.execute(
        "INSERT INTO recipes (name, why, steps, ingredients_used, recipe_ingredients, time_limit, diet, nutrition, language) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, why, json.dumps(steps), ingredients_used,
         json.dumps(recipe_ingredients) if recipe_ingredients else None,
         time_limit, diet, nutrition, language),
    )
    conn.commit()
    rid = cur.lastrowid
    conn.close()
    return rid


def get_history(limit: int = 50, favorites_only: bool = False) -> list[dict]:
    conn = _conn()
    if favorites_only:
        rows = conn.execute(
            "SELECT * FROM recipes WHERE is_favorite = 1 ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM recipes ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["steps"] = json.loads(d["steps"]) if isinstance(d["steps"], str) else d["steps"]
        result.append(d)
    return result


def toggle_favorite(recipe_id: int) -> None:
    conn = _conn()
    conn.execute(
        "UPDATE recipes SET is_favorite = CASE WHEN is_favorite = 1 THEN 0 ELSE 1 END WHERE id = ?",
        (recipe_id,),
    )
    conn.commit()
    conn.close()


def set_rating(recipe_id: int, rating: int) -> None:
    conn = _conn()
    conn.execute("UPDATE recipes SET rating = ? WHERE id = ?", (rating, recipe_id))
    conn.commit()
    conn.close()


def delete_recipe(recipe_id: int) -> None:
    conn = _conn()
    conn.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    conn.commit()
    conn.close()


def clear_history() -> None:
    conn = _conn()
    conn.execute("DELETE FROM recipes")
    conn.commit()
    conn.close()


# ── Saved dishes ────────────────────────────────────────────────────────────

def save_dish(name: str, ingredients: list[str], steps: list[str],
              notes: str = "", dietary_tags: list[str] | None = None) -> None:
    conn = _conn()
    conn.execute(
        "INSERT INTO saved_dishes (name, ingredients, steps, notes, dietary_tags) VALUES (?, ?, ?, ?, ?)",
        (name, json.dumps(ingredients), json.dumps(steps), notes,
         json.dumps(dietary_tags) if dietary_tags else None),
    )
    conn.commit()
    conn.close()


def get_saved_dishes() -> list[dict]:
    conn = _conn()
    rows = conn.execute("SELECT * FROM saved_dishes ORDER BY created_at DESC").fetchall()
    conn.close()
    return [_parse_dish(r) for r in rows]


def get_dish_by_id(dish_id: int) -> dict | None:
    conn = _conn()
    row = conn.execute("SELECT * FROM saved_dishes WHERE id = ?", (dish_id,)).fetchone()
    conn.close()
    return _parse_dish(row) if row else None


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
    conn = _conn()
    conn.execute("UPDATE saved_dishes SET rating = ? WHERE id = ?", (rating, dish_id))
    conn.commit()
    conn.close()


def delete_dish(dish_id: int) -> None:
    conn = _conn()
    conn.execute("DELETE FROM saved_dishes WHERE id = ?", (dish_id,))
    conn.commit()
    conn.close()


def _parse_dish(row) -> dict:
    d = dict(row)
    d["ingredients"] = json.loads(d["ingredients"]) if isinstance(d.get("ingredients"), str) else d.get("ingredients", [])
    d["steps"] = json.loads(d["steps"]) if isinstance(d.get("steps"), str) else d.get("steps", [])
    tags = d.get("dietary_tags")
    d["dietary_tags"] = json.loads(tags) if isinstance(tags, str) else (tags or [])
    return d


# ── Preferences ─────────────────────────────────────────────────────────────

def get_pref(key: str, default: str | None = None) -> str | None:
    conn = _conn()
    row = conn.execute("SELECT value FROM preferences WHERE key = ?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else default


def set_pref(key: str, value: str) -> None:
    conn = _conn()
    conn.execute("INSERT OR REPLACE INTO preferences (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def get_taste_profile() -> tuple[list[dict], list[dict]]:
    conn = _conn()
    liked = conn.execute(
        "SELECT name, why FROM recipes WHERE rating = 1 ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    disliked = conn.execute(
        "SELECT name FROM recipes WHERE rating = -1 ORDER BY created_at DESC LIMIT 5"
    ).fetchall()
    conn.close()
    return [dict(r) for r in liked], [dict(r) for r in disliked]
