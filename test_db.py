import os
import tempfile
import pytest

# Use a temp DB for tests
import db


@pytest.fixture(autouse=True)
def _use_temp_db(tmp_path, monkeypatch):
    test_db = str(tmp_path / "test_dinner.db")
    monkeypatch.setattr(db, "DB_PATH", test_db)
    db.init_db()
    yield


def test_init_db_creates_tables():
    conn = db._conn()
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    names = {t["name"] for t in tables}
    assert "recipes" in names
    assert "saved_dishes" in names
    assert "preferences" in names
    conn.close()


def test_save_and_get_recipe():
    rid = db.save_recipe("Pasta", "Quick", ["Boil", "Serve"], "pasta", "15 min", "Any", "350 kcal", "en", ["pasta", "tomato"])
    assert rid is not None
    history = db.get_history()
    assert len(history) == 1
    assert history[0]["name"] == "Pasta"
    assert history[0]["recipe_ingredients"] is not None


def test_toggle_favorite():
    rid = db.save_recipe("Soup", "Warm", ["Boil"], "carrot", "30 min", "Any", None, "en", ["carrot"])
    db.toggle_favorite(rid)
    row = [r for r in db.get_history() if r["id"] == rid][0]
    assert row["is_favorite"] == 1
    db.toggle_favorite(rid)
    row2 = [r for r in db.get_history() if r["id"] == rid][0]
    assert row2["is_favorite"] == 0


def test_set_rating():
    rid = db.save_recipe("Curry", "Spicy", ["Cook"], "chicken", "30 min", "High protein", None, "en", ["chicken"])
    db.set_rating(rid, 1)
    liked, disliked = db.get_taste_profile()
    assert len(liked) == 1
    assert liked[0]["name"] == "Curry"
    db.set_rating(rid, -1)
    liked2, disliked2 = db.get_taste_profile()
    assert len(liked2) == 0
    assert len(disliked2) == 1


def test_delete_recipe():
    rid = db.save_recipe("X", "Y", ["Z"], "a", "15 min", "Any", None, "en")
    db.delete_recipe(rid)
    assert len(db.get_history()) == 0


def test_clear_history():
    db.save_recipe("A", "B", ["C"], "d", "15 min", "Any", None, "en")
    db.save_recipe("E", "F", ["G"], "h", "30 min", "Any", None, "en")
    assert len(db.get_history()) == 2
    db.clear_history()
    assert len(db.get_history()) == 0


def test_save_and_get_dish():
    db.save_dish("Mapo Tofu", ["tofu", "doubanjiang"], ["Fry", "Simmer"], "Classic Sichuan")
    dishes = db.get_saved_dishes()
    assert len(dishes) == 1
    assert dishes[0]["name"] == "Mapo Tofu"
    assert dishes[0]["ingredients"] == ["tofu", "doubanjiang"]


def test_delete_dish():
    db.save_dish("Test", ["a"], ["b"], "")
    dishes = db.get_saved_dishes()
    did = dishes[0]["id"]
    db.delete_dish(did)
    assert len(db.get_saved_dishes()) == 0


def test_preferences():
    assert db.get_pref("lang", "en") == "en"
    db.set_pref("lang", "zh")
    assert db.get_pref("lang", "en") == "zh"
