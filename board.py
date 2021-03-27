from __future__ import annotations

from logging import getLogger
from random import shuffle
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from card import PURPLE, YELLOW

if TYPE_CHECKING:
    from telegram import User

    from card import Card
    from game import Game
    from player import Player


class Board:
    purple: Optional[Card] = None
    yellow: Dict[Player, List[Card]] = {}
    loser: Optional[User] = None

    def __init__(self, game):
        self.game: Game = game
        self.init()

        self.logger = getLogger(__name__)

    def init(self):
        self.loser = None
        self.purple = None
        self.yellow = {}
        for player in self.game.players:
            if player != self.game.current_player:
                self.yellow[player] = []
        order = list(range(1, len(self.yellow.keys()) + 1))
        shuffle(order)
        self.order = order

    def play_card_by(self, player: Player, card: Card):
        """Called from Player.play"""
        if player == self.game.current_player:
            self.logger.info(f"{card.color} == {PURPLE}")
            self.logger.info(f"{self.purple} is None")
            self.purple = card
            [self.game.purple_deck.draw() for _ in range(2)]

            self.game.logger.info(f"{self.purple} {self.purple.space}")

            self.game.state += 1

            self.logger.info(f"{self.game.state} == {self.game.State.YELLOW}")
        else:
            self.logger.info(f"{card.color} == {YELLOW}")

            self.yellow[player].append(card)
            if self.is_others_played:
                self.game.state += 1

    @property
    def is_others_played(self) -> bool:
        for cards in self.yellow.values():
            if len(cards) != self.purple.space:
                return False
        return True

    def get_cards(self) -> List[Tuple[str, List[Card]]]:
        return [
            (str(i + 1), x)
            for i, (_, x) in enumerate(sorted(zip(self.order, self.yellow.values())))
        ]

    def get_players(self) -> List[Tuple[str, Player]]:
        return [
            (str(i + 1), x)
            for i, (_, x) in enumerate(sorted(zip(self.order, self.yellow.keys())))
        ]

    def get_loser(self, selected: int) -> Player:
        index = self.order.index(selected)
        return list(self.yellow.keys())[index]
