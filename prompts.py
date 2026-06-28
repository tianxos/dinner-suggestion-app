from __future__ import annotations

TIME_MAP_ZH = {"15 min": "15 分钟", "30 min": "30 分钟", "60 min": "60 分钟"}
DIET_MAP_ZH = {
    "Any": "不限",
    "Vegetarian": "素食",
    "Low carb": "低碳水",
    "High protein": "高蛋白",
    "Pescatarian": "鱼素",
}


def build_prompt(
    ingredients: str,
    time_limit: str,
    diet: str,
    language: str,
    nonce: int,
    saved_dishes: list[dict] | None = None,
    taste_traits: str | None = None,
) -> str:
    if language == "zh":
        return _build_zh(ingredients, time_limit, diet, nonce, saved_dishes, taste_traits)
    return _build_en(ingredients, time_limit, diet, nonce, saved_dishes, taste_traits)


def _build_en(
    ingredients: str,
    time_limit: str,
    diet: str,
    nonce: int,
    saved_dishes: list[dict] | None,
    taste_traits: str | None,
) -> str:
    parts = [
        "You are a practical home-cooking assistant. Suggest dinners someone can",
        "cook RIGHT NOW with what they have.\n",
        "Constraints:",
        "- Suggest EXACTLY 2 recipes.",
        f"- Each must be realistically completable within {time_limit}.",
        "- Prefer common household ingredients; assume basics like salt, pepper,",
        "  oil, and water are available.",
        "- Do NOT require specialty tools or rare/hard-to-find ingredients.",
        "- Keep instructions simple and actionable: at most 6 short steps each.",
        "- List 4 to 8 key ingredients per recipe (exclude pantry staples like",
        "  salt, oil, water).",
        "- Include an estimated nutrition line per serving (calories, protein,",
        "  carbs). Be approximate but realistic.",
        "- Prioritise simplicity over creativity. No long essays, no alternatives,",
        "  no filler.",
        "- Western/international style preferred (pasta, stir-fry, salads, soups,",
        "  tacos, casseroles, etc.).",
    ]
    if diet != "Any":
        parts.append(f"- Dietary preference: {diet}.")
    if taste_traits:
        parts.append(f"- The user tends to prefer dishes like: {taste_traits}.")
    if saved_dishes:
        names = [d["name"] for d in saved_dishes]
        parts.append(
            f"- The user also enjoys these dishes (suggest variations or similar"
            f" styles): {', '.join(names)}."
        )
    parts.append(f"\nIngredients the user has: {ingredients}")
    parts.append(f"\n(variation seed: {nonce})")
    return "\n".join(parts)


def _build_zh(
    ingredients: str,
    time_limit: str,
    diet: str,
    nonce: int,
    saved_dishes: list[dict] | None,
    taste_traits: str | None,
) -> str:
    t = TIME_MAP_ZH.get(time_limit, time_limit)
    d = DIET_MAP_ZH.get(diet, diet)

    parts = [
        "你是一位实用的家庭烹饪助手。请根据用户现有的食材推荐晚餐菜谱。\n",
        "要求：",
        "- 推荐**恰好 2 道**菜。",
        f"- 每道菜必须在 {t} 内能完成。",
        "- 优先使用常见食材；假设盐、酱油、油、水等基础调料都有。",
        "- 不要要求特殊工具或稀有食材。",
        "- 步骤要简单实用，每道菜最多 6 步。",
        "- 每道菜列出 4-8 种关键食材（不包括盐、油、水等基础调料）。",
        "- 每道菜提供估算营养信息（每份的热量、蛋白质、碳水），可以粗略但要合理。",
        "- 优先做中餐/亚洲风格的菜式（炒菜、汤面、盖饭、蒸菜等）。",
        "- 荤素搭配合理，注意营养均衡。",
        "- 优先选用当季时令食材。",
        "- 简洁为主，不要长篇大论。",
    ]
    if diet != "Any":
        parts.append(f"- 饮食偏好：{d}。")
    if taste_traits:
        parts.append(f"- 用户偏爱类似这样的菜：{taste_traits}。")
    if saved_dishes:
        names = [d["name"] for d in saved_dishes]
        parts.append(f"- 用户还喜欢以下菜品（可推荐变体或类似风格）：{'、'.join(names)}。")
    parts.append(f"\n用户现有的食材：{ingredients}")
    parts.append(f"\n(随机种子：{nonce})")
    return "\n".join(parts)
