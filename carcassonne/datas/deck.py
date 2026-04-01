"""
This module defines the Deck class used to manage Carcassonne tiles.
It includes tile initialization, deterministic shuffling, and draw helpers.
"""

import random


class Deck:
    """Represent the draw pile and tile order for a game."""

    @staticmethod
    def _shuffle_fisher_yates_in_place(
        items: list[str], rng: random.Random
    ) -> None:
        for i in range(len(items) - 1, 0, -1):
            j = rng.randrange(i + 1)
            items[i], items[j] = items[j], items[i]

    @staticmethod
    def _shuffle_naive_in_place(items: list[str], rng: random.Random) -> None:
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
        """
        Draw and return the top tile from the deck.

        Returns:
            The drawn tile string, or None if the deck is empty
        """
        if not self.tiles:
            if not silent:
                print("Deck is empty, cannot draw a tile.")
            return None
        return self.tiles.pop()

    def draw_river_tile(self, silent: bool = False) -> str | None:
        """
        Draw and return the next river tile from the river tile list.

        Returns:
            The drawn river tile string, or None if no river tiles remain
        """
        if not self.river_tiles:
            if not silent:
                print("No more river tiles available.")
            return None
        return self.river_tiles.pop(0)

    def append(self, tile):
        self.tiles = [tile] + self.tiles

    def len(self) -> int:
        """Return the number of tiles currently left in the deck."""
        return len(self.tiles)

    def len_river(self) -> int:
        """Return the number of tiles currently left in the river deck."""
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

        # Shuffle river tiles, keeping the last tile (FFSF) fixed at the end.
        river_len = len(self.river_tiles) - 1
        for i in range(river_len - 1, 0, -1):
            if seed_index + 1 < len(seed_list):
                j = (
                    int(
                        str(seed_list[seed_index])
                        + str(seed_list[seed_index + 1])
                    )
                    * 123
                    % (i + 1)
                )
                seed_index += 1
            else:
                j = (
                    int(str(seed_list[seed_index]) + str(seed_list[0]))
                    * 123
                    % (i + 1)
                )
                seed_index = 0
            self.river_tiles[i], self.river_tiles[j] = self.river_tiles[j], self.river_tiles[i]

    def shuffle_naive(self, seed: int) -> None:
        """
        Shuffle the deck with a deterministic naive swap strategy.

        Args:
            seed: Seed used to generate pseudo-random swap indices
        """
        rng = random.Random(seed)
        self._shuffle_naive_in_place(self.tiles, rng)

        if len(self.river_tiles) > 1:
            river_prefix = self.river_tiles[:-1]
            self._shuffle_naive_in_place(river_prefix, rng)
            self.river_tiles[:-1] = river_prefix

        # Shuffle river tiles, keeping the last tile (FFSF) fixed at the end.
        river_len = len(self.river_tiles) - 1
        n_river = river_len
        for i in range(n_river):
            if seed_index + 1 < len(seed_list):
                j = (
                    int(
                        str(seed_list[seed_index])
                        + str(seed_list[seed_index + 1])
                    )
                    * 123
                    % n_river
                )
                seed_index += 1
            else:
                j = (
                    int(str(seed_list[seed_index]) + str(seed_list[0]))
                    * 123
                    % n_river
                )
                seed_index = 0
            self.river_tiles[i], self.river_tiles[j] = self.river_tiles[j], self.river_tiles[i]

    def is_empty(self) -> bool:
        """Return True when no tile remains in the deck."""
        if not self.tiles:
            return True
        else:
            return False
