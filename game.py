import logging
from typing import Optional

from board import Board
from card import PURPLE_CARDS, YELLOW_CARDS
from config import ADMIN_LIST, OPEN_LOBBY
from deck import Deck


class Game:
    current_player: Optional["User"] = None  # who choose a purple color
    starter: Optional["User"] = None
    started = False
    open = OPEN_LOBBY

    def __init__(self, chat):
        self.chat = chat

        self.yellow_deck = Deck()
        self.purple_deck = Deck()
        self.board = Board(self)

        self.logger = logging.getLogger(__name__)

    def start(self):
        self.yellow_deck.init(YELLOW_CARDS.copy())
        self.purple_deck.init(PURPLE_CARDS.copy())
        self.board.init()

        self.started = True

        for player in self.players:
            player.draw_first_hand()

    def turn(self):
        self.current_player = self.current_player.next
        for player in self.players:
            player.draw()
        self.board.init()

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

    def get_loser(self):
        count = self.get_end_count()
        for player in self.players:
            if -player.score >= count:
                return player
        return None

    def get_winners(self) -> list:
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
