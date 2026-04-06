from collections import Counter
from itertools import product
from unittest.mock import patch

from carcassonne.datas.deck import Deck


def _shuffle_small_deck_with_forced_choices(
    method_name: str, choices: tuple[int, ...]
) -> tuple[str, ...]:
    deck = Deck()
    deck.tiles = ["A", "B", "C"]
    deck.river_tiles = ["R_END"]
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
