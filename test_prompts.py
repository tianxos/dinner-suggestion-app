from prompts import build_prompt


def test_english_prompt_basic():
    p = build_prompt("chicken, rice", "30 min", "Any", "en", 42)
    assert "EXACTLY 2 recipes" in p
    assert "30 min" in p
    assert "chicken, rice" in p
    assert "variation seed: 42" in p


def test_english_prompt_diet():
    p = build_prompt("eggs", "15 min", "Vegetarian", "en", 1)
    assert "Vegetarian" in p


def test_english_prompt_taste_traits():
    p = build_prompt("pasta", "60 min", "Any", "en", 1, taste_traits="spicy Thai, ramen")
    assert "spicy Thai" in p


def test_english_prompt_saved_dishes():
    saved = [{"name": "Kung Pao Chicken"}, {"name": "Mapo Tofu"}]
    p = build_prompt("chicken, tofu", "30 min", "Any", "en", 1, saved_dishes=saved)
    assert "Kung Pao Chicken" in p
    assert "Mapo Tofu" in p


def test_chinese_prompt_basic():
    p = build_prompt("jirou, mifan", "30 min", "Any", "zh", 42)
    assert "2 道" in p
    assert "30 分钟" in p
    assert "jirou, mifan" in p


def test_chinese_prompt_diet():
    p = build_prompt("egg", "15 min", "Low carb", "zh", 1)
    assert "低碳水" in p


def test_chinese_prompt_taste():
    p = build_prompt("tofu", "60 min", "Any", "zh", 1, taste_traits="麻辣")
    assert "麻辣" in p


def test_chinese_prompt_saved_dishes():
    saved = [{"name": "宫保鸡丁"}, {"name": "麻婆豆腐"}]
    p = build_prompt("chicken", "30 min", "Any", "zh", 1, saved_dishes=saved)
    assert "宫保鸡丁" in p
    assert "麻婆豆腐" in p


def test_chinese_prompt_time_map():
    p = build_prompt("rice", "60 min", "Any", "zh", 1)
    assert "60 分钟" in p
    p2 = build_prompt("rice", "15 min", "Any", "zh", 1)
    assert "15 分钟" in p2
