from __future__ import annotations

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
from google.genai import errors as genai_errors

from db import (
    init_db,
    save_recipe,
    get_history,
    toggle_favorite,
    set_rating,
    delete_recipe,
    clear_history,
    save_dish,
    get_saved_dishes,
    get_dish_by_id,
    search_dishes_by_ingredients,
    set_dish_rating,
    delete_dish,
    get_pref,
    set_pref,
    get_taste_profile,
)
from gemini_client import generate_recipes
from i18n import t as _i18n

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Dinner Suggester", page_icon="\U0001f373", layout="centered")

# ── One-time DB init ────────────────────────────────────────────────────────
init_db()

# ── Session state defaults ─────────────────────────────────────────────────
if "lang" not in st.session_state:
    st.session_state["lang"] = get_pref("lang", "en")


def L(key: str) -> str:
    return _i18n(key, st.session_state["lang"])


# ── CSS ─────────────────────────────────────────────────────────────────────
st.markdown(
    """<style>
      .stApp { background-color: #FFF8F0; color: #1A0F0A; }
      [data-testid="stHeader"] { background-color: #FFF8F0 !important; }
      [data-testid="stToolbar"] { background-color: #FFF8F0 !important; }
      [data-testid="stToolbar"] button { color: #1A0F0A !important; }
      [data-testid="stHeaderActionButtons"] { background-color: #FFF8F0 !important; }
      [data-testid="stHeaderActionButtons"] button { color: #1A0F0A !important; }
      [data-testid="stToolbar"] [data-baseweb="popover"] { color: #1A0F0A !important; background-color: #FFF8F0 !important; }
      [data-testid="stToolbar"] [data-baseweb="menu"] { background-color: #FFF8F0 !important; }
      [data-testid="stToolbar"] [data-baseweb="menu"] li,
      [data-testid="stToolbar"] [data-baseweb="menu"] div,
      [data-testid="stToolbar"] [data-baseweb="menu"] span,
      [data-testid="stToolbar"] [data-baseweb="menu"] a,
      [data-testid="stToolbar"] [role="menuitem"],
      [data-testid="stToolbar"] [role="menuitem"] span,
      [data-testid="stToolbar"] [role="menuitem"] div { color: #1A0F0A !important; background-color: transparent !important; }
      [data-testid="stToolbar"] [role="menuitem"]:hover { background-color: #F0E6DA !important; }
      [data-testid="stToolbar"] [role="menuitem"] * { color: #1A0F0A !important; }
      .block-container { padding-top: 3.5rem; padding-bottom: 2rem; max-width: 640px; }
      html { font-size: 18px; }
      @media (max-width: 480px) { html { font-size: 20px; } }
      textarea, input, select { font-size: 1.2rem !important; }
      label, .stMarkdown, p, li, .stText, .stCaption, .stRadio label, .stSelectbox label,
      div[data-testid="stMarkdownContainer"] p, div[data-testid="stMarkdownContainer"] li,
      div[data-testid="stMarkdownContainer"] div, .st-emotion-cache-10trblm, .st-emotion-cache-16txtl3,
      .stButton button, .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
          color: #1A0F0A; font-size: 1.2rem !important; line-height: 1.6; font-weight: 500;
      }
      div.stButton > button {
          width: 100%; padding: 0.5rem 1rem; font-size: 1.1rem !important;
          font-weight: 700; border-radius: 10px; border: none;
          background-color: #E85D3A; color: white;
          box-shadow: 0 2px 10px rgba(232,93,58,0.3);
      }
      div.stButton > button:hover { background-color: #D44A28; color: white; border: none; }
      div.stButton > button:active { background-color: #C13E1E; }
      h1 { color: #1A0F0A !important; font-size: 1.6rem !important; font-weight: 700 !important; }
      h3 { color: #1A0F0A !important; font-size: 1.5rem !important; font-weight: 700 !important; }
      .stCaption { font-size: 1.15rem !important; color: #4A3728 !important; }
      div[data-testid="stRadio"] > label { font-size: 1.15rem !important; padding: 0.6rem 1rem !important; min-width: auto; }
      div[data-testid="stRadio"] > label > div { font-size: 1.15rem !important; }
      div[data-testid="stExpander"] summary { font-size: 1.15rem !important; background-color: #FFF8F0 !important; color: #1A0F0A !important; }
      div[data-testid="stExpander"] summary p { color: #1A0F0A !important; }
      div[data-testid="stTab"] button { color: #1A0F0A !important; font-weight: 600 !important; }
      div[data-testid="stTab"] button[aria-selected="true"] { color: #E85D3A !important; border-bottom-color: #E85D3A !important; }
      div[data-testid="stSelectbox"] div[data-baseweb="select"] { min-height: 3rem !important; padding: 0.5rem 1rem !important; min-width: 220px !important; }
      div[data-testid="stSelectbox"] div[data-baseweb="select"] > div { font-size: 1rem !important; }
      div[data-testid="stSelectbox"] label { font-size: 1.15rem !important; }
      div[data-testid="stSelectbox"] div[role="listbox"] { min-width: 220px !important; }
      .dish-card { padding: 1rem; border-radius: 12px; border: 1px solid #E8D5C4; margin-bottom: 0.5rem; background: #FFFCF8; }
      .rating-btn { display: inline-block; padding: 0.3rem 0.8rem; border-radius: 8px; border: 2px solid #E8D5C4; cursor: pointer; margin: 0 0.2rem; font-size: 1.1rem; }
      .rating-btn.active { border-color: #E85D3A; background: #FFF0EC; }
      .match-badge { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.9rem; font-weight: 600; }
      .match-high { background: #D4EDDA; color: #155724; }
      .match-med { background: #FFF3CD; color: #856404; }
      .match-low { background: #F8D7DA; color: #721C24; }
      [data-testid="stHorizontalBlock"] > div { padding-left: 0.3rem !important; padding-right: 0.3rem !important; }
      [data-testid="stHorizontalBlock"] .stButton { margin-bottom: 0 !important; }
      [data-testid="stHorizontalBlock"] .stButton button { padding: 0.4rem 0.8rem !important; font-size: 0.95rem !important; }
      /* Dialog / modal popup */
      [data-testid="stDialog"] { background-color: #FFF8F0 !important; color: #1A0F0A !important; }
      [data-testid="stDialog"] div, [data-testid="stDialog"] p, [data-testid="stDialog"] li,
      [data-testid="stDialog"] span, [data-testid="stDialog"] h1, [data-testid="stDialog"] h2,
      [data-testid="stDialog"] h3, [data-testid="stDialog"] h4, [data-testid="stDialog"] h5,
      [data-testid="stDialog"] h6, [data-testid="stDialog"] label, [data-testid="stDialog"] caption {
          color: #1A0F0A !important; background-color: transparent !important;
      }
      [data-testid="stDialog"] [data-testid="stMarkdownContainer"] p,
      [data-testid="stDialog"] [data-testid="stMarkdownContainer"] li,
      [data-testid="stDialog"] [data-testid="stMarkdownContainer"] div {
          color: #1A0F0A !important;
      }
      [data-testid="stDialog"] button { color: #1A0F0A !important; }
      [data-testid="stDialog"] [data-testid="stModal"] {
          background-color: #FFF8F0 !important;
      }
      section[data-testid="stDialog"] { background-color: rgba(0,0,0,0.4) !important; }
      section[data-testid="stDialog"] > div { background-color: #FFF8F0 !important; color: #1A0F0A !important; }
      section[data-testid="stDialog"] div, section[data-testid="stDialog"] p,
      section[data-testid="stDialog"] span, section[data-testid="stDialog"] label,
      section[data-testid="stDialog"] h1, section[data-testid="stDialog"] h2,
      section[data-testid="stDialog"] h3, section[data-testid="stDialog"] h4 {
          color: #1A0F0A !important;
      }
    </style>""",
    unsafe_allow_html=True,
)

# ── Header with language toggle ─────────────────────────────────────────────
_header_cols = st.columns([0.75, 0.25])
with _header_cols[1]:
    prev_lang = st.session_state["lang"]
    lang = st.selectbox(
        "Language",
        ["en", "zh"],
        format_func=lambda x: "English" if x == "en" else "\u4e2d\u6587",
        key="lang_selector",
        label_visibility="collapsed",
    )
    if lang != prev_lang:
        st.session_state["lang"] = lang
        set_pref("lang", lang)
        st.rerun()

# ── Tabs ────────────────────────────────────────────────────────────────────
tab_suggest, tab_pantry, tab_planner, tab_history, tab_my_dishes = st.tabs(
    [L("tab_suggest"), L("tab_pantry"), L("tab_planner"), L("tab_history"), L("tab_my_dishes")]
)

# =============================================================================
# TAB 1 — Suggest
# =============================================================================
with tab_suggest:
    st.title(L("title"))
    st.caption(L("subtitle"))

    ingredients = st.text_area(
        L("ingredients_label"),
        placeholder=L("ingredients_placeholder"),
        height=110,
        key="ingredients",
    )

    time_limit = st.radio(
        L("time_label"),
        ["15 min", "30 min", "60 min"],
        format_func=lambda x: L(f"time_{x.split()[0]}"),
        horizontal=True,
        index=1,
        key="time",
    )

    with st.expander(L("diet_expander")):
        diet = st.selectbox(
            L("diet_label"),
            ["Any", "Vegetarian", "Low carb", "High protein", "Pescatarian"],
            format_func=lambda x: L(f"diet_{x.lower().replace(' ', '_')}"),
            index=0,
            key="diet",
        )

    suggest = st.button(L("suggest_button"), type="primary")

    # ── Generate & store ─────────────────────────────────────────
    def run_and_store() -> None:
        text = (st.session_state.get("ingredients") or "").strip()
        if not text:
            st.session_state["error"] = L("error_no_ingredients")
            st.session_state["recipes"] = None
            return
        try:
            with st.spinner(L("spinner_text")):
                tl = st.session_state.get("time", "30 min")
                dt = st.session_state.get("diet", "Any")
                lang = st.session_state["lang"]

                saved = get_saved_dishes() if get_pref("include_saved", "1") == "1" else []
                liked, disliked = get_taste_profile()
                taste_traits = ", ".join(r["name"] for r in liked[:3]) if liked else None

                recipes = generate_recipes(text, tl, dt, lang, saved, taste_traits)

                for r in recipes:
                    save_recipe(
                        r.name, r.why, r.steps, text, tl, dt,
                        getattr(r, "nutrition", None), lang,
                        getattr(r, "ingredients", None),
                    )

                st.session_state["recipes"] = recipes
                st.session_state["error"] = None
        except genai_errors.APIError as exc:
            st.session_state["recipes"] = None
            st.session_state["error"] = L("error_api").format(msg=str(exc))
        except Exception as exc:
            st.session_state["recipes"] = None
            st.session_state["error"] = L("error_generic").format(msg=str(exc))

    if suggest:
        run_and_store()

    # ── Error display ────────────────────────────────────────────
    if st.session_state.get("error"):
        err = st.session_state["error"]
        if "429" in err or "RESOURCE_EXHAUSTED" in err:
            st.error("Daily API quota exhausted. Please try again tomorrow or upgrade your Gemini API plan.")
        else:
            st.warning(err)

    # ── Recipe results ───────────────────────────────────────────
    recipes = st.session_state.get("recipes")
    if recipes:
        for i, recipe in enumerate(recipes, start=1):
            st.subheader(f"{i}. {recipe.name}")
            st.markdown(f"*{recipe.why}*")

            # Nutrition
            if recipe.nutrition:
                st.caption(f"\U0001f4ca {recipe.nutrition}")

            # Steps
            for sn, step in enumerate(recipe.steps, start=1):
                st.markdown(f"**{sn}.** {step}")

            # Action buttons row
            btn_cols = st.columns(4)
            with btn_cols[0]:
                if st.button(L("share_copy"), key=f"share_{i}"):
                    share_text = f"{recipe.name}\n{recipe.why}\n\n"
                    share_text += "\n".join(f"{sn}. {step}" for sn, step in enumerate(recipe.steps, start=1))
                    if recipe.nutrition:
                        share_text += f"\n\n{L('nutrition_label')}: {recipe.nutrition}"
                    st.code(share_text, language=None)
            with btn_cols[1]:
                if st.button(L("cooking_mode"), key=f"cook_{i}"):
                    st.session_state["cooking_recipe"] = recipe
                    st.session_state["cooking_step"] = 0
                    st.rerun()
            with btn_cols[2]:
                if recipe.ingredients:
                    if st.button(L("grocery_title"), key=f"grocery_{i}"):
                        st.session_state["show_grocery"] = i
                        st.rerun()

            # Grocery list display
            if st.session_state.get("show_grocery") == i and recipe.ingredients:
                user_ings = [x.strip().lower() for x in st.session_state.get("ingredients", "").split(",") if x.strip()]
                have = []
                need = []
                for ing in recipe.ingredients:
                    ing_lower = ing.lower()
                    if any(u in ing_lower or ing_lower in u for u in user_ings):
                        have.append(ing)
                    else:
                        need.append(ing)
                st.markdown(f"**{L('grocery_title')}**")
                if have:
                    st.markdown(f"**{L('grocery_you_have')}:** {', '.join(have)}")
                if need:
                    st.markdown(f"**{L('grocery_you_need')}:** {', '.join(need)}")
                    grocery_text = "\n".join(f"[ ] {x}" for x in need)
                    if st.button(L("grocery_copy"), key=f"gcopy_{i}"):
                        st.code(grocery_text, language=None)
                        st.success(L("grocery_copied"))
                if st.button("X Close", key=f"gclose_{i}"):
                    st.session_state.pop("show_grocery", None)
                    st.rerun()

            if i < len(recipes):
                st.divider()
        st.button(L("regenerate_button"), on_click=run_and_store)

    # ── Cooking mode dialog ──────────────────────────────────────
    if st.session_state.get("cooking_recipe"):
        _cook = st.session_state["cooking_recipe"]
        _step_idx = st.session_state.get("cooking_step", 0)

        st.subheader(L("cooking_mode"))
        st.markdown(f"### {_cook.name}")
        st.markdown(f"**{L('cooking_step').format(n=_step_idx + 1)}** of {len(_cook.steps)}")

        st.markdown(
            f"<div style='font-size:2rem;line-height:1.8;padding:1.5rem;"
            f"background:#FFF8F0;border-radius:14px;border:2px solid #E85D3A;'>"
            f"{_cook.steps[_step_idx]}</div>",
            unsafe_allow_html=True,
        )

        nav_cols = st.columns([0.3, 0.4, 0.3])
        with nav_cols[0]:
            if _step_idx > 0:
                if st.button(L("cooking_prev"), key="cook_prev"):
                    st.session_state["cooking_step"] = _step_idx - 1
                    st.rerun()
        with nav_cols[1]:
            if _step_idx == len(_cook.steps) - 1:
                if st.button(L("cooking_done"), key="cook_done"):
                    st.session_state.pop("cooking_recipe", None)
                    st.session_state.pop("cooking_step", None)
                    st.rerun()
        with nav_cols[2]:
            if _step_idx < len(_cook.steps) - 1:
                if st.button(L("cooking_next"), key="cook_next"):
                    st.session_state["cooking_step"] = _step_idx + 1
                    st.rerun()

        st.button(L("cooking_exit"), key="cook_exit", on_click=lambda: (
            st.session_state.pop("cooking_recipe", None),
            st.session_state.pop("cooking_step", None),
        ))

    # ── Taste profile ────────────────────────────────────────────
    liked, disliked = get_taste_profile()
    if liked:
        names = [r["name"] for r in liked]
        st.caption(f"{L('pref_learned')}: {', '.join(names)}")
    else:
        st.caption(L("pref_empty"))

# =============================================================================
# TAB 2 — Pantry
# =============================================================================
with tab_pantry:
    st.subheader(L("pantry_title"))
    st.caption(L("pantry_subtitle"))

    pantry_ings = st.text_area(
        L("pantry_input_label"),
        placeholder=L("pantry_placeholder"),
        height=110,
        key="pantry_ingredients",
    )

    if st.button(L("pantry_find"), type="primary", key="pantry_find_btn"):
        raw = (pantry_ings or "").strip()
        if raw:
            user_list = [x.strip() for x in raw.replace("\n", ",").split(",") if x.strip()]
            matches = search_dishes_by_ingredients(user_list)
            st.session_state["pantry_matches"] = matches
            st.session_state["pantry_user_ings"] = user_list
        else:
            st.session_state["pantry_matches"] = []

    matches = st.session_state.get("pantry_matches")
    if matches is not None:
        if not matches:
            st.warning(L("pantry_no_match"))
        else:
            st.markdown(f"**{L('pantry_match_header')}** ({len(matches)} dishes)")
            user_ings = st.session_state.get("pantry_user_ings", [])
            for dish, score in matches[:10]:
                total_ings = max(len(dish.get("ingredients", [])), 1)
                pct = min(score, total_ings)
                badge_cls = "match-high" if pct >= 3 else ("match-med" if pct >= 2 else "match-low")
                with st.container():
                    c1, c2 = st.columns([0.8, 0.2])
                    with c1:
                        st.markdown(f"**{dish['name']}**")
                        st.caption(f"{dish.get('notes', '')}")
                        # Show matched ingredients
                        dish_ings_lower = [i.lower() for i in dish.get("ingredients", [])]
                        matched_names = []
                        for u in user_ings:
                            for di in dish.get("ingredients", []):
                                if u.lower() in di.lower() or di.lower() in u.lower():
                                    if di not in matched_names:
                                        matched_names.append(di)
                        if matched_names:
                            st.caption(f"\u2705 {', '.join(matched_names[:5])}")
                    with c2:
                        st.markdown(
                            f"<span class='match-badge {badge_cls}'>"
                            f"{L('pantry_match_score').format(n=pct, total=total_ings)}</span>",
                            unsafe_allow_html=True,
                        )
                    bc1, bc2 = st.columns(2)
                    with bc1:
                        if st.button(L("pantry_cooking_mode"), key=f"pantry_cook_{dish['id']}"):
                            st.session_state["cooking_recipe"] = type("R", (), {
                                "name": dish["name"],
                                "steps": dish.get("steps", []),
                                "ingredients": dish.get("ingredients", []),
                            })()
                            st.session_state["cooking_step"] = 0
                            st.rerun()
                    with bc2:
                        if st.button(L("recipe_detail_view"), key=f"pantry_detail_{dish['id']}"):
                            st.session_state["view_dish"] = dish["id"]
                            st.rerun()
                    st.divider()

# =============================================================================
# TAB 3 — Meal Planner
# =============================================================================
with tab_planner:
    st.subheader(L("planner_title"))
    st.caption(L("planner_subtitle"))

    if st.button(L("planner_gen_button"), type="primary", key="planner_gen"):
        try:
            with st.spinner(L("planner_spinner")):
                saved = get_saved_dishes()
                liked, _ = get_taste_profile()
                taste_traits = ", ".join(r["name"] for r in liked[:5]) if liked else None
                lang = st.session_state["lang"]

                from gemini_client import get_client, MODEL, use_zen
                import random, time
                # Build a custom prompt requesting 7 different dinners for the week
                if lang == "zh":
                    prompt = (
                        "你是一位实用的家庭烹饪助手。请为用户规划一周七天的晚餐。\n\n"
                        "要求：\n"
                        "- 推荐**恰好 14 道**菜，每天 2 道不同的菜。\n"
                        "- 优先使用常见食材；假设盐、酱油、油、水等基础调料都有。\n"
                        "- 不要要求特殊工具或稀有食材。\n"
                        "- 步骤要简单实用，每道菜最多 6 步。\n"
                        "- 每道菜列出 4-8 种关键食材。\n"
                        "- 优先做中餐/亚洲风格的菜式。\n"
                        "- 每天的两道菜要搭配合理（一荤一素、一菜一汤等），注意营养均衡。\n"
                        "- 优先选用当季时令食材。\n"
                        "- 14 道菜要各不相同。\n"
                    )
                else:
                    prompt = (
                        "You are a practical home-cooking assistant. Plan 7 days of dinners for the week.\n\n"
                        "Constraints:\n"
                        "- Suggest EXACTLY 14 recipes: 2 different dishes per day for 7 days.\n"
                        "- Prefer common household ingredients; assume salt, oil, water are available.\n"
                        "- Keep instructions simple: at most 6 short steps each.\n"
                        "- List 4 to 8 key ingredients per recipe.\n"
                        "- Western/international style preferred (pasta, salads, soups,\n"
                        "  tacos, casseroles, etc.).\n"
                        "- Each day's 2 dishes should complement each other (e.g. one meat + one veggie).\n"
                        "- All 14 dishes must be different from each other.\n"
                    )
                if taste_traits:
                    prompt += f"\nThe user tends to prefer: {taste_traits}.\n"
                if saved:
                    names = [d["name"] for d in saved[:10]]
                    prompt += f"The user also enjoys: {', '.join(names)}.\n"
                nonce = random.randint(1, 1_000_000)
                attempt_prompt = prompt + f"\n(variation seed: {nonce})"

                from models import WeeklyPlan, Recipe

                progress = st.empty()
                progress.caption("🤔 正在思考一周菜单...")

                if use_zen():
                    import os as _os
                    from gemini_client import get_zen_client, _extract_json
                    zen = get_zen_client()
                    zen_prompt = (
                        attempt_prompt
                        + "\n\nYou MUST respond with valid JSON only, no markdown. "
                        'Return: {"recipes": [{"name": "...", "why": "...", '
                        '"ingredients": ["..."], "steps": ["..."], "nutrition": "..."}]}'
                    )
                    stream = zen.chat.completions.create(
                        model=_os.getenv("ZEN_MODEL", "mimo-v2.5-free"),
                        messages=[{"role": "user", "content": zen_prompt}],
                        temperature=0.9,
                        stream=True,
                    )
                    text = ""
                    last_update = time.time()
                    for chunk in stream:
                        delta = chunk.choices[0].delta.content or ""
                        text += delta
                        now = time.time()
                        if now - last_update >= 2.0:
                            progress.caption(f"🤔 正在思考中... (已生成 {len(text)} 字符)")
                            last_update = now
                    progress.caption(f"✅ 思考完成，正在整理...")
                    data = _extract_json(text)
                    if isinstance(data, dict) and "recipes" in data:
                        plan = [Recipe(**r) for r in data["recipes"]]
                    else:
                        raise ValueError(f"Unexpected JSON structure from Zen: {type(data)}")
                else:
                    from google.genai import types
                    client = get_client()
                    stream = client.models.generate_content_stream(
                        model=MODEL,
                        contents=attempt_prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=WeeklyPlan,
                            temperature=0.9,
                        ),
                    )
                    text = ""
                    last_update = time.time()
                    for chunk in stream:
                        text += chunk.text or ""
                        now = time.time()
                        if now - last_update >= 2.0:
                            progress.caption(f"🤔 正在思考中... (已生成 {len(text)} 字符)")
                            last_update = now
                    progress.caption(f"✅ 思考完成，正在整理...")
                    plan = WeeklyPlan.model_validate_json(text).recipes

                progress.empty()

                if len(plan) != 14:
                    raise ValueError(
                        f"Model returned {len(plan)} recipes instead of 14. Please try again."
                    )
                st.session_state["meal_plan"] = plan
                st.session_state["meal_plan_error"] = None
        except Exception as exc:
            st.session_state["meal_plan"] = None
            st.session_state["meal_plan_error"] = str(exc)

    plan_err = st.session_state.get("meal_plan_error")
    if plan_err:
        if "429" in plan_err or "RESOURCE_EXHAUSTED" in plan_err:
            st.error("Daily API quota exhausted. Please try again tomorrow or upgrade your Gemini API plan.")
        else:
            st.warning(f"Error: {plan_err}")

    plan = st.session_state.get("meal_plan")
    if plan:
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        if st.session_state.get("lang") == "zh":
            days = ["\u5468\u4e00", "\u5468\u4e8c", "\u5468\u4e09", "\u5468\u56db", "\u5468\u4e94", "\u5468\u516d", "\u5468\u65e5"]

        all_ingredients = []
        recipes_per_day = 2
        for day_idx in range(7):
            day = days[day_idx] if day_idx < len(days) else f"Day {day_idx+1}"
            day_recipes = plan[day_idx * recipes_per_day : (day_idx + 1) * recipes_per_day]
            if not day_recipes:
                continue
            dish_names = " + ".join(r.name for r in day_recipes)
            with st.expander(f"{day}: {dish_names}", expanded=(day_idx == 0)):
                for ri, recipe in enumerate(day_recipes):
                    if ri > 0:
                        st.markdown("---")
                    st.markdown(f"**{recipe.name}**")
                    st.markdown(f"*{recipe.why}*")
                    if recipe.nutrition:
                        st.caption(f"\U0001f4ca {recipe.nutrition}")
                    for sn, step in enumerate(recipe.steps, start=1):
                        st.markdown(f"**{sn}.** {step}")
                    if st.button(L("cooking_mode"), key=f"plan_cook_{day_idx}_{ri}"):
                        st.session_state["cooking_recipe"] = recipe
                        st.session_state["cooking_step"] = 0
                        st.rerun()
                    if recipe.ingredients:
                        all_ingredients.extend(recipe.ingredients)

        # Combined grocery list
        if all_ingredients:
            st.divider()
            st.subheader(L("planner_grocery"))
            deduped = list(dict.fromkeys(all_ingredients))
            grocery_text = "\n".join(f"[ ] {x}" for x in deduped)
            st.code(grocery_text, language=None)
            if st.button(L("grocery_copy"), key="plan_grocery_copy"):
                st.success(L("grocery_copied"))

        st.button(L("planner_regenerate"), key="plan_regen")

# =============================================================================
# TAB 4 — History
# =============================================================================
with tab_history:
    st.subheader(L("history_title"))
    show_fav_only = st.checkbox(L("history_filter_favorites"), key="history_fav_filter")

    history = get_history(favorites_only=show_fav_only)
    if not history:
        st.caption(L("history_empty"))
    else:
        for row in history:
            with st.container():
                cols = st.columns([0.6, 0.15, 0.15, 0.1])
                with cols[0]:
                    st.markdown(f"**{row['name']}**")
                    preview = (row["why"][:120] + "\u2026") if len(row["why"]) > 120 else row["why"]
                    st.caption(preview)
                    st.caption(f"{row['time_limit']} \u00b7 {row['diet']} \u00b7 {row['created_at'][:10]}")
                with cols[1]:
                    label = L("favorite") if row["is_favorite"] else L("not_favorite")
                    if st.button(label, key=f"fav_{row['id']}"):
                        toggle_favorite(row["id"])
                        st.rerun()
                with cols[2]:
                    if st.button("\U0001f44d", key=f"like_{row['id']}"):
                        set_rating(row["id"], 1)
                        st.rerun()
                with cols[3]:
                    if st.button("\U0001f5d1\ufe0f", key=f"del_{row['id']}"):
                        delete_recipe(row["id"])
                        st.rerun()
            st.divider()

        if st.button(L("history_clear"), key="clear_history"):
            clear_history()
            st.rerun()

# =============================================================================
# TAB 5 — My Dishes (with ratings, filters, sorting, detail dialog)
# =============================================================================
with tab_my_dishes:
    st.subheader(L("my_dishes_title"))

    with st.expander(L("my_dishes_import")):
        dish_name = st.text_input(L("my_dishes_name"), key="dish_name")
        dish_ingredients = st.text_area(L("my_dishes_ingredients"), height=100, key="dish_ingredients")
        dish_steps = st.text_area(L("my_dishes_steps"), height=100, key="dish_steps")
        dish_notes = st.text_area(L("my_dishes_notes"), height=60, key="dish_notes")
        if st.button(L("my_dishes_save"), key="save_dish"):
            name = (dish_name or "").strip()
            if name:
                ings = [l.strip() for l in dish_ingredients.strip().split("\n") if l.strip()]
                stps = [l.strip() for l in dish_steps.strip().split("\n") if l.strip()]
                save_dish(name, ings, stps, dish_notes.strip())
                st.success(L("my_dishes_saved"))
                st.rerun()

    saved_dishes = get_saved_dishes()
    if not saved_dishes:
        st.caption(L("my_dishes_empty"))
    else:
        # Filter & sort controls
        fc1, fc2 = st.columns(2)
        with fc1:
            filter_tag = st.selectbox(
                L("my_dishes_filter"),
                ["all", "Spicy", "Vegetarian", "Quick", "Comfort food", "Kid-friendly"],
                format_func=lambda x: L("my_dishes_filter_all") if x == "all" else x,
                key="dish_filter",
            )
        with fc2:
            sort_by = st.selectbox(
                L("my_dishes_sort"),
                ["recent", "rating", "name"],
                format_func=lambda x: L(f"my_dishes_sort_{x}"),
                key="dish_sort",
            )

        # Apply filters
        filtered = saved_dishes
        if filter_tag != "all":
            filtered = [d for d in filtered if filter_tag.lower() in [t.lower() for t in (d.get("dietary_tags") or [])]]

        # Apply sort
        if sort_by == "rating":
            filtered.sort(key=lambda d: -(d.get("rating") or 0))
        elif sort_by == "name":
            filtered.sort(key=lambda d: d["name"])
        # else "recent" = default order

        for dish in filtered:
            with st.container():
                # Title + rating + view on one row
                rc1, rc2, rc3 = st.columns([0.5, 0.25, 0.25])
                with rc1:
                    st.markdown(f"**{dish['name']}**")
                    if dish.get("notes"):
                        st.caption(dish["notes"])
                    tags = dish.get("dietary_tags") or []
                    if tags:
                        st.caption(" ".join(f"`{t}`" for t in tags))
                with rc2:
                    current_rating = dish.get("rating") or 0
                    rating_label = L("rating_loved") if current_rating == 1 else (L("rating_none") if current_rating == 0 else L("rating_bad"))
                    if st.button(rating_label, key=f"dish_rate_{dish['id']}"):
                        new_rating = 1 if current_rating == 0 else (-1 if current_rating == 1 else 0)
                        set_dish_rating(dish["id"], new_rating)
                        st.rerun()
                with rc3:
                    if st.button(L("recipe_detail_view"), key=f"dish_view_{dish['id']}"):
                        st.session_state["view_dish"] = dish["id"]
                        st.rerun()

                # Cook + delete on one row
                bc1, bc2 = st.columns(2)
                with bc1:
                    if st.button(L("pantry_cooking_mode"), key=f"dish_cook_{dish['id']}"):
                        st.session_state["cooking_recipe"] = type("R", (), {
                            "name": dish["name"],
                            "steps": dish.get("steps", []),
                            "ingredients": dish.get("ingredients", []),
                        })()
                        st.session_state["cooking_step"] = 0
                        st.rerun()
                with bc2:
                    if st.button(L("my_dishes_delete"), key=f"dish_del_{dish['id']}"):
                        delete_dish(dish["id"])
                        st.rerun()

                st.caption("")

# ── Recipe Detail Dialog ─────────────────────────────────────────────────────
@st.dialog(L("recipe_detail"), width="large")
def show_dish_detail(dish_id: int):
    dish = get_dish_by_id(dish_id)
    if not dish:
        st.error("Dish not found")
        return

    st.markdown(f"### {dish['name']}")
    if dish.get("notes"):
        st.caption(dish["notes"])
    tags = dish.get("dietary_tags") or []
    if tags:
        st.caption(" ".join(f"`{t}`" for t in tags))

    ings = dish.get("ingredients", [])
    if ings:
        st.markdown(f"**{L('ingredients_label')}:**")
        st.markdown(", ".join(ings))

    steps = dish.get("steps", [])
    if steps:
        st.markdown(f"**{L('cooking_mode')}:**")
        for sn, step in enumerate(steps, start=1):
            st.markdown(f"**{sn}.** {step}")

    ac1, ac2 = st.columns(2)
    with ac1:
        if st.button(L("recipe_detail_cooking"), key="detail_cook", use_container_width=True):
            st.session_state["cooking_recipe"] = type("R", (), {
                "name": dish["name"],
                "steps": dish.get("steps", []),
                "ingredients": dish.get("ingredients", []),
            })()
            st.session_state["cooking_step"] = 0
            st.rerun()
    with ac2:
        if st.button(L("recipe_detail_share"), key="detail_share", use_container_width=True):
            share_text = f"{dish['name']}\n\n"
            if ings:
                share_text += f"{L('ingredients_label')}: {', '.join(ings)}\n\n"
            share_text += "\n".join(f"{sn}. {step}" for sn, step in enumerate(steps, start=1))
            st.code(share_text, language=None)

if st.session_state.get("view_dish"):
    show_dish_detail(st.session_state.pop("view_dish"))
