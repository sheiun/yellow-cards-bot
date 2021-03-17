from __future__ import annotations

import logging

from card import YELLOW
from errors import TooManyCardsError, NotEnoughPlayersError


class Player:
    """
    This class represents a player.
    It is basically a circular doubly-linked list.
    On initialization, it will connect itself to a game and its
    other players by placing itself behind the current player.
    """

    def __init__(self, game, user):
        self.game = game
        self.user = user

        self.discard_amount = 0
        self.cards = []
        self.purple_cards = []
        self.score = 0

        self.logger = logging.getLogger(__name__)

        # Check if this player is the first player in this game.
        if game.current_player:
            self.next = game.current_player
            self.prev = game.current_player.prev
            game.current_player.prev.next = self
            game.current_player.prev = self
        else:
            self.next = self
            self.prev = self
            game.current_player = self

    @property
    def left(self) -> Player:
        return self.prev

    @property
    def right(self) -> Player:
        return self.next

    @property
    def front(self) -> Player:
        if len(self.game.players) < 4:
            raise NotEnoughPlayersError()
        if len(self.game.players) <= 7:
            return self.next.next
        return self.next.next.next

    def draw_first_hand(self):
        for _ in range(13):
            self.cards.append(self.game.yellow_deck.draw())

    def leave(self):
        """Removes player from the game and closes the gap in the list"""
        if self.next is self:
            return

        self.next.prev = self.prev
        self.prev.next = self.next
        self.next = None
        self.prev = None

        self.cards = []
        self.discard_amount = 0

    def __repr__(self):
        return repr(self.user)

    def __str__(self):
        return str(self.user)

    def draw(self):
        while len(self.cards) < 13:
            self.cards.append(self.game.yellow_deck.draw())

    def play(self, card: "Card"):
        """Plays a card and removes it from hand"""
        if card.color == YELLOW:
            if len(self.game.board.yellow[self]) >= self.game.board.purple.space:
                raise TooManyCardsError()
            self.cards.remove(card)
        self.game.board.play_card_by(self, card)

    def discard(self, card: "Card"):
        if self.discard_amount == 0:
            # TODO:
            raise Exception("You can't disacrd!")
        self.cards.remove(card)

    @property
    def discarded(self) -> bool:
        # own cards + played cards + discarded cards == 13
        return (
            len(self.cards) == 13 - self.game.board.purple.space - self.discard_amount
        )

    @property
    def can_play(self) -> bool:
        """Player can play a yellow card"""
        purple_card = self.game.board.purple
        return (
            self.game.current_player != self
            and purple_card is not None
            and purple_card.space > len(self.game.board.yellow[self])
        )
