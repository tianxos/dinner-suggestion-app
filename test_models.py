import json
import pytest
from models import Recipe, RecipeSuggestions


def test_recipe_basic():
    r = Recipe(name="Stir-fry", why="Quick and easy", steps=["Chop", "Cook", "Serve"], ingredients=["chicken", "soy sauce"], nutrition="400 kcal")
    assert r.name == "Stir-fry"
    assert len(r.steps) == 3
    assert r.nutrition == "400 kcal"
    assert r.ingredients == ["chicken", "soy sauce"]


def test_recipe_optional_fields():
    r = Recipe(name="Soup", why="Warm", steps=["Boil"], ingredients=["carrot"])
    assert r.nutrition is None


def test_recipe_from_dict():
    data = {
        "name": "Noodles",
        "why": "Fast",
        "steps": ["Boil noodles", "Add sauce"],
        "ingredients": ["noodles", "soy sauce", "garlic"],
        "nutrition": "350 kcal, 12g protein, 50g carbs",
    }
    r = Recipe(**data)
    assert r.name == "Noodles"
    assert len(r.ingredients) == 3


def test_recipe_suggestions_validation():
    data = {
        "recipes": [
            {"name": "A", "why": "a", "steps": ["s1"], "ingredients": ["i1"]},
            {"name": "B", "why": "b", "steps": ["s2", "s3"], "ingredients": ["i2"]},
        ]
    }
    suggestions = RecipeSuggestions(**data)
    assert len(suggestions.recipes) == 2
    assert suggestions.recipes[0].name == "A"


def test_recipe_suggestions_from_json():
    json_str = json.dumps({
        "recipes": [
            {"name": "Fried Rice", "why": "Uses leftover rice", "steps": ["Heat oil", "Add rice", "Stir"], "ingredients": ["rice", "egg", "soy sauce"]},
        ]
    })
    suggestions = RecipeSuggestions.model_validate_json(json_str)
    assert suggestions.recipes[0].name == "Fried Rice"
    assert suggestions.recipes[0].ingredients == ["rice", "egg", "soy sauce"]
