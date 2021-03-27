from json import load
from typing import Any, Dict

STICKERS_DICT = load(open("stickers.json"))
PURPLE_SPACE_LIST = load(open("purple_space.json"))

PURPLE = "purple"
YELLOW = "yellow"

PURPLE_CARD = "紫牌 🟪"
YELLOW_CARD = "黃牌 🟨"

COLOR_ICONS = {PURPLE: "🟪", YELLOW: "🟨"}


class Card:
    def __init__(self, color: str, sticker: Dict[str, Any], *args, **kwargs):
        self.color = color
        self.sticker = sticker
        if color == PURPLE:
            self.space:int = kwargs.pop("space", 1)

    def __eq__(self, obj):
        return isinstance(obj, Card) and self.sticker["id"] == obj.sticker["id"]

    @staticmethod
    def from_id(id: str):
        # TODO: refactor it to resolve time complexity
        for card in YELLOW_CARDS + PURPLE_CARDS:
            if str(card.sticker["id"]) == id:
                return card
        # TODO: create a error class
        raise Exception("Card not found!")

    def __repr__(self):
        return f"{COLOR_ICONS[self.color]} ({str(self)})"

    def __str__(self):
        return str(self.sticker["id"])


PURPLE_CARDS = [
    Card(PURPLE, sticker, space=space)
    for sticker, space in zip(STICKERS_DICT[PURPLE], PURPLE_SPACE_LIST)
]
YELLOW_CARDS = [Card(YELLOW, sticker) for sticker in STICKERS_DICT[YELLOW]]


print("[INFO] Cards loaded")
del STICKERS_DICT, PURPLE_SPACE_LIST
