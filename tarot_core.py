"""Card data and drawing rules, deliberately independent of Streamlit."""

from __future__ import annotations

import json
import random
from pathlib import Path
from urllib.request import Request, urlopen

DATA_DIR = Path(__file__).resolve().parent / "data"
SNAPSHOT = DATA_DIR / "cards_waite.json"
SOURCE_URL = "https://raw.githubusercontent.com/StarTarotOnline/tarot-rws-dataset/7f8ab42b62eef5d018536b8775010e3d6e61eb27/data/cards.jsonl"
IMAGE_URL = "https://petaloverflow.github.io/tarot-api/cards/"

MAJOR_ZH = [
    "愚者", "魔术师", "女祭司", "皇后", "皇帝", "教皇", "恋人", "战车", "力量", "隐者",
    "命运之轮", "正义", "倒吊人", "死神", "节制", "恶魔", "高塔", "星星", "月亮", "太阳", "审判", "世界",
]
SUITS = {"wands": ("权杖", "wa"), "cups": ("圣杯", "cu"),
         "swords": ("宝剑", "sw"), "pentacles": ("星币", "pe")}
RANKS = {1: "首牌", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七",
         8: "八", 9: "九", 10: "十", 11: "侍从", 12: "骑士", 13: "皇后", 14: "国王"}


def card_from_source(record: dict) -> dict:
    """Keep verbatim original Waite language, with separate Chinese names."""
    arcana = record["arcana"]
    number = int(record["number"])
    if arcana == "major":
        name_zh, image_code = MAJOR_ZH[number], f"ar{number:02d}.jpg"
    else:
        suit_name, prefix = SUITS[record["suit"]]
        name_zh, image_code = suit_name + RANKS[number], f"{prefix}{number:02d}.jpg"
    meanings = record["divinatory_meanings"]
    return {
        "id": record["card_id"],
        "name": record["name"],
        "name_zh": name_zh,
        "arcana": arcana,
        "suit": record["suit"],
        "image": IMAGE_URL + image_code,
        "waite_upright": meanings["upright"],
        "waite_reversed": meanings["reversed"],
        "additional_upright": meanings.get("additional_upright"),
        "additional_reversed": meanings.get("additional_reversed"),
    }


def validate_cards(cards: list[dict]) -> list[dict]:
    if len(cards) != 78 or len({card["id"] for card in cards}) != 78:
        raise ValueError("牌库应包含 78 张唯一的卡牌")
    for card in cards:
        if not all(card.get(k) for k in ("name", "name_zh", "waite_upright", "waite_reversed", "image")):
            raise ValueError(f"牌库记录不完整：{card.get('id')}")
    return cards


def load_cards() -> list[dict]:
    """Prefer a checked-in offline snapshot; download and cache it only if absent."""
    if SNAPSHOT.exists():
        return validate_cards(json.loads(SNAPSHOT.read_text(encoding="utf-8")))
    request = Request(SOURCE_URL, headers={"User-Agent": "Tarot-Reader/2.0"})
    with urlopen(request, timeout=15) as response:
        records = [json.loads(line) for line in response.read().decode("utf-8").splitlines() if line.strip()]
    cards = validate_cards([card_from_source(record) for record in records])
    # Streamlit cloud may have a read-only or short-lived filesystem. The app still works
    # without writing; the first successfully fetched result is cached by Streamlit.
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        SNAPSHOT.write_text(json.dumps(cards, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError:
        pass
    return cards


def draw(cards: list[dict], number: int = 3, rng=None) -> list[dict]:
    """Sample without replacement; upright/reversed probability is 50% each."""
    if not 1 <= number <= min(78, len(cards)):
        raise ValueError("抽牌数须在 1 至牌库大小之间")
    rng = rng or random.SystemRandom()
    return [
        {"id": card["id"], "name": card["name"], "name_zh": card["name_zh"],
         "orientation": rng.choice(("正位", "逆位"))}
        for card in rng.sample(cards, number)
    ]
