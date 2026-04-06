from collections import Counter

from carcassonne.datas.deck import Deck


def test_shuffle_fisher_yates_is_deterministic_for_same_seed():
    seed = 12345678
    deck_a = Deck()
    deck_b = Deck()

    deck_a.shuffle_fisher_yates(seed)
    deck_b.shuffle_fisher_yates(seed)

    assert deck_a.tiles == deck_b.tiles
    assert deck_a.river_tiles == deck_b.river_tiles


def test_shuffle_naive_is_deterministic_for_same_seed():
    seed = 87654321
    deck_a = Deck()
    deck_b = Deck()

    deck_a.shuffle_naive(seed)
    deck_b.shuffle_naive(seed)

    assert deck_a.tiles == deck_b.tiles
    assert deck_a.river_tiles == deck_b.river_tiles


def test_shuffle_fisher_yates_preserves_tile_multiset():
    deck = Deck()
    original_tiles = Counter(deck.tiles)
    original_river_tiles = Counter(deck.river_tiles)
    last_river_tile = deck.river_tiles[-1]

    deck.shuffle_fisher_yates(12345678)

    assert Counter(deck.tiles) == original_tiles
    assert Counter(deck.river_tiles) == original_river_tiles
    assert deck.river_tiles[-1] == last_river_tile


def test_shuffle_naive_preserves_tile_multiset():
    deck = Deck()
    original_tiles = Counter(deck.tiles)
    original_river_tiles = Counter(deck.river_tiles)
    last_river_tile = deck.river_tiles[-1]

    deck.shuffle_naive(12345678)

    assert Counter(deck.tiles) == original_tiles
    assert Counter(deck.river_tiles) == original_river_tiles
    assert deck.river_tiles[-1] == last_river_tile

def test_draw_and_draw_river_tile_report_empty_sources(capsys):
    deck = Deck()
    deck.tiles = []
    deck.river_tiles = []

    assert deck.draw() is None
    assert deck.draw_river_tile() is None

    captured = capsys.readouterr()
    assert "Deck is empty" in captured.out
    assert "No more river tiles" in captured.out


def test_append_prepends_tile_and_is_empty_reflects_current_state():
    deck = Deck()
    deck.tiles = []

    assert deck.is_empty() is True

    deck.append("CFFF")

    assert deck.tiles == ["CFFF"]
    assert deck.is_empty() is False
