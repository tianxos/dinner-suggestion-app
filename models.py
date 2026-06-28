from __future__ import annotations

from pydantic import BaseModel, Field


class Recipe(BaseModel):
    name: str = Field(description="Short, appetizing meal name.")
    why: str = Field(description="One short sentence on why it fits the ingredients and time.")
    ingredients: list[str] = Field(description="4 to 8 key ingredients needed (excluding pantry basics like salt, oil, water).")
    steps: list[str] = Field(description="3 to 6 short, actionable cooking steps. No filler.")
    nutrition: str | None = Field(default=None, description="Estimated calories/protein/carbs per serving, e.g. '420 kcal, 30g protein, 45g carbs'.")


class RecipeSuggestions(BaseModel):
    recipes: list[Recipe] = Field(description="Exactly two recipe suggestions.")


class WeeklyPlan(BaseModel):
    recipes: list[Recipe] = Field(
        min_length=14,
        max_length=14,
        description="Exactly fourteen recipe suggestions: two per day for seven days.",
    )
