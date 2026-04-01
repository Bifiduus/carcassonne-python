from collections import Counter
from itertools import product
from unittest.mock import patch

from carcassonne.datas.deck import Deck


def test_shuffle_fisher_yates_is_deterministic_for_same_seed():
    seed = 12345678
    deck_a = Deck()
    deck_b = Deck()

    deck_a.shuffle_fisher_yates(seed)
    deck_b.shuffle_fisher_yates(seed)

    assert deck_a.tiles == deck_b.tiles


def test_shuffle_naive_is_deterministic_for_same_seed():
    seed = 87654321
    deck_a = Deck()
    deck_b = Deck()

    deck_a.shuffle_naive(seed)
    deck_b.shuffle_naive(seed)

    assert deck_a.tiles == deck_b.tiles


def test_shuffle_fisher_yates_preserves_tile_multiset():
    deck = Deck()
    original_tiles = Counter(deck.tiles)

    deck.shuffle_fisher_yates(12345678)

    assert Counter(deck.tiles) == original_tiles


def test_shuffle_naive_preserves_tile_multiset():
    deck = Deck()
    original_tiles = Counter(deck.tiles)

    deck.shuffle_naive(12345678)

    assert Counter(deck.tiles) == original_tiles


def _shuffle_small_deck_with_forced_choices(
    method_name: str, choices: tuple[int, ...]
) -> tuple[str, ...]:
    deck = Deck()
    deck.tiles = ["A", "B", "C"]
    remaining_choices = iter(choices)

    class FakeRandom:
        def __init__(self, seed: int) -> None:
            self.seed = seed

        def randrange(self, upper_bound: int) -> int:
            choice = next(remaining_choices)
            assert 0 <= choice < upper_bound
            return choice

    with patch("carcassonne.datas.deck.random.Random", FakeRandom):
        getattr(deck, method_name)(12345678)

    return tuple(deck.tiles)


def _chi_square_uniformity(counts: Counter[tuple[str, ...]]) -> float:
    expected = sum(counts.values()) / len(counts)
    return sum((count - expected) ** 2 / expected for count in counts.values())


def test_shuffle_fisher_yates_is_exactly_uniform_on_three_tiles():
    counts: Counter[tuple[str, ...]] = Counter()

    for choices in product(range(3), range(2)):
        permutation = _shuffle_small_deck_with_forced_choices(
            "shuffle_fisher_yates", choices
        )
        counts[permutation] += 1

    assert len(counts) == 6
    assert set(counts.values()) == {1}
    assert _chi_square_uniformity(counts) == 0


def test_shuffle_naive_is_less_uniform_than_fisher_yates_on_three_tiles():
    counts: Counter[tuple[str, ...]] = Counter()

    for choices in product(range(3), repeat=3):
        permutation = _shuffle_small_deck_with_forced_choices(
            "shuffle_naive", choices
        )
        counts[permutation] += 1

    assert len(counts) == 6
    assert len(set(counts.values())) > 1
    assert _chi_square_uniformity(counts) > 0
