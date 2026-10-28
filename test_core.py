import unittest
from tarot_core import MAJOR_ZH, card_from_source, draw, validate_cards


class TestTarotCore(unittest.TestCase):
    def test_major_image_and_name(self):
        card = card_from_source({
            "arcana": "major", "number": 0, "suit": None,
            "name": "The Fool", "card_id": "00-fool",
            "divinatory_meanings": {"upright": "Folly", "reversed": "Negligence"},
        })
        self.assertEqual(card["name_zh"], "愚者")
        self.assertTrue(card["image"].endswith("ar00.jpg"))
        self.assertEqual(card["waite_upright"], "Folly")

    def test_minor_image_and_name(self):
        card = card_from_source({
            "arcana": "minor", "number": 12, "suit": "swords",
            "name": "Knight of Swords", "card_id": "swords/knight-of-swords",
            "divinatory_meanings": {"upright": "X", "reversed": "Y"},
        })
        self.assertEqual(card["name_zh"], "宝剑骑士")
        self.assertTrue(card["image"].endswith("sw12.jpg"))

    def test_draw_unique_and_orientation(self):
        import random
        cards = [{"id": str(i), "name": str(i), "name_zh": str(i)} for i in range(78)]
        result = draw(cards, 3, random.Random(77))
        self.assertEqual(len({card["id"] for card in result}), 3)
        self.assertTrue(all(card["orientation"] in ("正位", "逆位") for card in result))
        self.assertEqual(len(MAJOR_ZH), 22)

    def test_all_78_generated_image_paths_are_unique(self):
        records = [
            {"arcana": "major", "number": n, "suit": None,
             "name": f"Major {n}", "card_id": f"major/{n}",
             "divinatory_meanings": {"upright": "X", "reversed": "Y"}}
            for n in range(22)
        ]
        for suit in ("wands", "cups", "swords", "pentacles"):
            records += [
                {"arcana": "minor", "number": n, "suit": suit,
                 "name": f"{suit} {n}", "card_id": f"{suit}/{n}",
                 "divinatory_meanings": {"upright": "X", "reversed": "Y"}}
                for n in range(1, 15)
            ]
        cards = validate_cards([card_from_source(record) for record in records])
        self.assertEqual(len({card["image"] for card in cards}), 78)
        self.assertEqual(len({card["name_zh"] for card in cards}), 78)

    def test_validate_rejects_incomplete(self):
        with self.assertRaises(ValueError):
            validate_cards([{"id": "duplicate"}] * 78)


if __name__ == "__main__":
    unittest.main()
