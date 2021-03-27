import unittest

from game import Game
from player import Player


class Test(unittest.TestCase):
    def setUp(self):
        self.game = Game(None)

    def test_insert(self):
        p0 = Player(self.game, "Player 0")
        p1 = Player(self.game, "Player 1")
        p2 = Player(self.game, "Player 2")

        self.assertEqual(p0, p2.next)
        self.assertEqual(p1, p0.next)
        self.assertEqual(p2, p1.next)

        self.assertEqual(p0.prev, p2)
        self.assertEqual(p1.prev, p0)
        self.assertEqual(p2.prev, p1)

    def test_leave(self):
        p0 = Player(self.game, "Player 0")
        p1 = Player(self.game, "Player 1")
        p2 = Player(self.game, "Player 2")

        p1.leave()

        self.assertEqual(p0, p2.next)
        self.assertEqual(p2, p0.next)

    def test_draw(self):
        p = Player(self.game, "Player 0")
        self.game.start()

        draw_count = 13

        self.assertEqual(len(p.cards), draw_count)

    def test_play(self):
        p = Player(self.game, "Player 0")
        p1 = Player(self.game, "Player 1")
        p2 = Player(self.game, "Player 2")

        self.game.start()

        p.play(p.cards[0])
        p1.play(p1.cards[0])
        p2.play(p2.cards[0])

