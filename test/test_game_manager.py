import unittest

from telegram import User, Chat

from game_manager import GameManager
from errors import AlreadyJoinedError, LobbyClosedError, NoGameInChatError, \
    NotEnoughPlayersError


class Test(unittest.TestCase):

    game = None

    def setUp(self):
        self.gm = GameManager()

        self.chat0 = Chat(0, 'group')
        self.chat1 = Chat(1, 'group')
        self.chat2 = Chat(2, 'group')

        self.user0 = User(0, 'user0', False)
        self.user1 = User(1, 'user1', False)
        self.user2 = User(2, 'user2', False)

    def test_new_game(self):
        g0 = self.gm.new_game(self.chat0)
        g1 = self.gm.new_game(self.chat1)

        self.assertListEqual(self.gm.chatid_games[0], [g0])
        self.assertListEqual(self.gm.chatid_games[1], [g1])

    def test_join_game(self):

        self.assertRaises(NoGameInChatError,
                          self.gm.join_game,
                          *(self.user0, self.chat0))

        g0 = self.gm.new_game(self.chat0)

        self.gm.join_game(self.user0, self.chat0)
        self.assertEqual(len(g0.players), 1)

        self.gm.join_game(self.user1, self.chat0)
        self.assertEqual(len(g0.players), 2)

        g0.open = False
        self.assertRaises(LobbyClosedError,
                          self.gm.join_game,
                          *(self.user2, self.chat0))

        g0.open = True
        self.assertRaises(AlreadyJoinedError,
                          self.gm.join_game,
                        *(self.user1, self.chat0))

    def test_leave_game(self):
        self.gm.new_game(self.chat0)

        self.gm.join_game(self.user0, self.chat0)
        self.gm.join_game(self.user1, self.chat0)

        self.assertRaises(NotEnoughPlayersError,
                          self.gm.leave_game,
                          *(self.user1, self.chat0))

        self.gm.join_game(self.user2, self.chat0)
        self.gm.leave_game(self.user0, self.chat0)

        self.assertRaises(NoGameInChatError,
                          self.gm.leave_game,
                          *(self.user0, self.chat0))

    def test_end_game(self):
        self.gm.new_game(self.chat0)

        self.gm.join_game(self.user0, self.chat0)
        self.gm.join_game(self.user1, self.chat0)

        self.assertEqual(len(self.gm.userid_players[0]), 1)

        self.gm.new_game(self.chat0)
        self.gm.join_game(self.user2, self.chat0)

        self.gm.end_game(self.chat0, self.user0)
        self.assertEqual(len(self.gm.chatid_games[0]), 1)

        self.gm.end_game(self.chat0, self.user2)
        self.assertFalse(0 in self.gm.chatid_games)
        self.assertFalse(0 in self.gm.userid_players)
        self.assertFalse(1 in self.gm.userid_players)
        self.assertFalse(2 in self.gm.userid_players)