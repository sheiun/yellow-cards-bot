import logging
from random import shuffle

from errors import DeckEmptyError


class Deck:
    def __init__(self):
        self.cards = []

        self.logger = logging.getLogger(__name__)
        self.logger.debug(self.cards)

    def init(self, cards: list):
        self.cards = cards
        shuffle(self.cards)

    def draw(self):
        if len(self.cards) > 0:
            card = self.cards.pop()
            self.logger.debug("Drawing card " + str(card))
            return card
        raise DeckEmptyError()
