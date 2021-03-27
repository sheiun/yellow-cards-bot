from __future__ import annotations

from logging import getLogger
from random import shuffle
from typing import TYPE_CHECKING, List

from errors import DeckEmptyError

if TYPE_CHECKING:
    from card import Card


class Deck:
    def __init__(self):
        self.cards = []

        self.logger = getLogger(__name__)
        self.logger.debug(self.cards)

    def init(self, cards: List[Card]):
        self.cards = cards
        shuffle(self.cards)

    def draw(self) -> Card:
        if len(self.cards) > 0:
            card = self.cards.pop()
            self.logger.debug("Drawing card " + str(card))
            return card
        raise DeckEmptyError()
