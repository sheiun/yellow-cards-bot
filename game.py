from __future__ import annotations

from enum import IntEnum
from logging import getLogger
from typing import TYPE_CHECKING, List, Optional

from board import Board
from card import PURPLE_CARDS, YELLOW_CARDS
from config import OPEN_LOBBY
from deck import Deck

if TYPE_CHECKING:
    from telegram import User

    from player import Player


class Game:
    class State(IntEnum):
        """The state represents current state"""

        START = 0
        PURPLE = 1
        YELLOW = 2
        LOSE = 3
        DISCARD = 4
        END = 5

    current_player: Optional[User] = None
    starter: Optional[User] = None
    state: Game.State = State.START
    open = OPEN_LOBBY

    def __init__(self, chat):
        self.chat = chat

        self.yellow_deck = Deck()
        self.purple_deck = Deck()
        self.board = Board(self)

        self.logger = getLogger(__name__)

    @property
    def started(self) -> bool:
        return self.state > Game.State.START

    @property
    def ended(self) -> bool:
        return self.state == Game.State.END

    def start(self):
        self.yellow_deck.init(YELLOW_CARDS.copy())
        self.purple_deck.init(PURPLE_CARDS.copy())
        self.board.init()

        self.state += 1
        self.logger.info(f"{self.state} == {self.State.PURPLE}")

        for player in self.players:
            player.draw_first_hand()

    def turn(self):
        self.current_player = self.current_player.next
        for player in self.players:
            player.draw()
        if self.board.loser:
            self.board.loser.discard_amount = 0
        self.board.init()
        self.state = self.State.PURPLE

    @property
    def players(self):
        if not self.current_player:
            return []

        players = []
        current_player = self.current_player
        itplayer = current_player.next
        players.append(current_player)
        while itplayer and itplayer is not current_player:
            players.append(itplayer)
            itplayer = itplayer.next
        return players

    def get_end_count(self) -> int:
        players_count = len(self.players)
        if players_count <= 5:
            return 6
        if players_count <= 7:
            return 5
        return 4

    def get_loser(self) -> Optional[Player]:
        count = self.get_end_count()
        for player in self.players:
            if -player.score >= count:
                return player
        return None

    def get_winners(self) -> List[Player]:
        loser = self.get_loser()
        if loser is None:
            # TODO: 建一個 winners haven't appeared error
            raise Exception("Game is not ended")

        highest_score = float("-inf")
        for player in self.players:
            if player.score > highest_score:
                highest_score = player.score

        winners = []
        for player in self.players:
            if player.score == highest_score:
                winners.append(player)

        return winners
