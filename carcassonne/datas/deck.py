"""
This module defines the Deck class used to manage Carcassonne tiles.
It includes tile initialization, deterministic shuffling, and draw helpers.
"""

import random

from carcassonne.i18n import gettext as _


class Deck:
    """Represent the draw pile and tile order for a game."""

    @staticmethod
    def _shuffle_fisher_yates_in_place(
        items: list[str], rng: random.Random
    ) -> None:
        """Shuffle a tile list in place with the Fisher-Yates algorithm.

        Args:
            items: Tile codes to reorder.
            rng: Random generator used to pick swap indices.

        Returns:
            None.
        """
        for i in range(len(items) - 1, 0, -1):
            j = rng.randrange(i + 1)
            items[i], items[j] = items[j], items[i]

    @staticmethod
    def _shuffle_naive_in_place(items: list[str], rng: random.Random) -> None:
        """Shuffle a tile list in place with repeated random swaps.

        Args:
            items: Tile codes to reorder.
            rng: Random generator used to pick swap indices.

        Returns:
            None.
        """
        n = len(items)
        for i in range(n):
            j = rng.randrange(n)
            items[i], items[j] = items[j], items[i]

    def __init__(self):
        """Initialize the deck with the base tile distribution."""
        self.tiles = [
            "FFFF/m",
            "FFFF/m",
            "FFFF/m",
            "FFFF/m",
            "FFFR/m",
            "FFFR/m",
            "CFFF",
            "CFFF",
            "CFFF",
            "CFFF",
            "CFFF",
            "FCFC/f",
            "FCFC/f",
            "FCFC/f",
            "CFCF/c",
            "CFCF/b",
            "CFCF/b",
            "CCCC/b",
            "FFCC",
            "FFCC",
            "CCFF",
            "CCFF",
            "CCFF",
            "CCFF/b",
            "CCFF/b",
            "CCCF",
            "CCCF",
            "CCCF",
            "CCCF/b",
            "CCCR",
            "CCCR/b",
            "CCCR/b",
            "FRFR",
            "FRFR",
            "FRFR",
            "FRFR",
            "FRFR",
            "FRFR",
            "FRFR",
            "FRFR",
            "FFRR",
            "FFRR",
            "FFRR",
            "FFRR",
            "FFRR",
            "FFRR",
            "FFRR",
            "FFRR",
            "FFRR",
            "CRFR",
            "CRFR",
            "CRFR",
            # "CRFR",
            "CFRR",
            "CFRR",
            "CFRR",
            "CRRF",
            "CRRF",
            "CRRF",
            "CCRR",
            "CCRR",
            "CCRR",
            "CCRR/b",
            "CCRR/b",
            "FRRR",
            "FRRR",
            "FRRR",
            "FRRR",
            "CRRR",
            "CRRR",
            "CRRR",
            "RRRR",
        ]
        self.river_tiles = [
            "FSRS/m",
            "FSFS",
            "FSFS",
            "FFSS",
            "FFSS",
            "CSCS",
            "CCSS",
            "CSRS",
            "RSRS",
            "RRSS",
            "FFSF",  # "FFSF",
        ]

    def draw(self, silent: bool = False) -> str | None:
        """Draw the next tile from the main deck.

        Args:
            silent: When True, do not print an error if the deck is empty.

        Returns:
            str | None: Drawn tile code, or None when no tile remains.
        """
        if not self.tiles:
            if not silent:
                print(_("Deck is empty, cannot draw a tile."))
            return None
        return self.tiles.pop()

    def draw_river_tile(self, silent: bool = False) -> str | None:
        """Draw the next tile from the river deck.

        Args:
            silent: When True, do not print an error if the river deck is
                empty.

        Returns:
            str | None: Drawn river tile code, or None when no river tile
                remains.
        """
        if not self.river_tiles:
            if not silent:
                print(_("No more river tiles available."))
            return None
        return self.river_tiles.pop(0)

    def append(self, tile):
        """Put one tile back on top of the main deck."""
        self.tiles = [tile] + self.tiles

    def len(self) -> int:
        """Return the number of tiles still available in the main deck."""
        return len(self.tiles)

    def len_river(self) -> int:
        """Return the number of tiles still available in the river deck."""
        return len(self.river_tiles)

    def shuffle_fisher_yates(self, seed: int) -> None:
        """
        Shuffle the deck with a deterministic Fisher-Yates algorithm.

        Args:
            seed: Seed used to generate pseudo-random swap indices
        """
        rng = random.Random(seed)
        self._shuffle_fisher_yates_in_place(self.tiles, rng)

        if len(self.river_tiles) > 1:
            river_prefix = self.river_tiles[:-1]
            self._shuffle_fisher_yates_in_place(river_prefix, rng)
            self.river_tiles[:-1] = river_prefix

    def shuffle_naive(self, seed: int) -> None:
        """Shuffle the deck with a deterministic naive swap strategy.

        Args:
            seed: Seed used to generate pseudo-random swap indices

        Returns:
            None.
        """
        rng = random.Random(seed)
        self._shuffle_naive_in_place(self.tiles, rng)

        if len(self.river_tiles) > 1:
            river_prefix = self.river_tiles[:-1]
            self._shuffle_naive_in_place(river_prefix, rng)
            self.river_tiles[:-1] = river_prefix

    def is_empty(self) -> bool:
        """Check whether the main deck contains any drawable tile.

        Returns:
            bool: True when `self.tiles` is empty.
        """
        if not self.tiles:
            return True
        else:
            return False
