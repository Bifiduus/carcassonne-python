import pytest
from carcassonne.datas.deck import Deck


class TestDeck:
    def test_deck_creation(self):
        deck = Deck()
        assert len(deck.tiles) == 71, "Deck should contain 71 tiles"

    def test_deck_shuffle(self):
        from carcassonne.datas.seed import Seed
        deck1 = Deck()
        deck2 = Deck()
        deck1.shuffle_fisher_yates(Seed().seed)
        assert deck1.tiles != deck2.tiles, "Shuffled deck should be different from unshuffled deck"
        deck1 = Deck()
        deck2 = Deck()
        deck1.shuffle_naive(Seed().seed)
        assert deck1.tiles != deck2.tiles, "Shuffled deck should be different from unshuffled deck"

    def test_deck_draw(self):
        deck = Deck()
        initial_length = len(deck.tiles)
        tile = deck.draw()
        assert tile is not None, "Drawn tile should not be None"
        assert len(deck.tiles) == initial_length - \
            1, "Deck should have one less tile after drawing"

    def test_deck_draw_empty(self, capfd):
        deck = Deck()
        for _ in range(len(deck.tiles)):
            deck.draw()
        tile = deck.draw()
        assert tile is None, "Drawing from an empty deck should return None"
        captured = capfd.readouterr()
        assert "Deck is empty, cannot draw a tile." in captured.out, "Should print a message when trying to draw from an empty deck"
