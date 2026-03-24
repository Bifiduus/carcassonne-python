"""
This module defines the Deck class used to manage Carcassonne tiles.
It includes tile initialization, deterministic shuffling, and draw helpers.
"""


class Deck:
    """Represent the draw pile and tile order for a game."""

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
            "FFSF",  # "FFSF",
            "FSFS", "FSFS",
            "FFSS", "FFSS",
            "CSCS",
            "CCSS",
            "CSRS",
            "RSRS",
            "RRSS"
        ]

    def draw(self) -> str | None:
        """
        Draw and return the top tile from the deck.

        Returns:
            The drawn tile string, or None if the deck is empty
        """
        if not self.tiles:
            print("Deck is empty, cannot draw a tile.")
            return None
        return self.tiles.pop()

    def draw_river_tile(self) -> str | None:
        """
        Draw and return the next river tile from the river tile list.

        Returns:
            The drawn river tile string, or None if no river tiles remain
        """
        if not self.river_tiles:
            print("No more river tiles available.")
            return None
        return self.river_tiles.pop(0)

    def len(self) -> int:
        """Return the number of tiles currently left in the deck."""
        return len(self.tiles)

    def shuffle_fisher_yates(self, seed: int) -> None:
        """
        Shuffle the deck with a deterministic Fisher-Yates algorithm.

        Args:
            seed: Seed used to generate pseudo-random swap indices
        """
        # Build deterministic pseudo-random indices from seed digits.
        seed_list: list[int] = [int(s) for s in str(seed)]
        seed_index = 0
        for i in range(len(self.tiles) - 1, 0, -1):
            # Fisher-Yates step: swap tile i with a tile in [0, i].
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
            self.tiles[i], self.tiles[j] = self.tiles[j], self.tiles[i]

    def shuffle_naive(self, seed: int) -> None:
        """
        Shuffle the deck with a deterministic naive swap strategy.

        Args:
            seed: Seed used to generate pseudo-random swap indices
        """
        seed_list: list[int] = [int(s) for s in str(seed)]
        seed_index = 0
        n = len(self.tiles)
        for i in range(n):
            if seed_index + 1 < len(seed_list):
                j = (
                    int(
                        str(seed_list[seed_index])
                        + str(seed_list[seed_index + 1])
                    )
                    * 123
                    % n
                )
                seed_index += 1
            else:
                j = (
                    int(str(seed_list[seed_index]) + str(seed_list[0]))
                    * 123
                    % n
                )
                seed_index = 0
            self.tiles[i], self.tiles[j] = self.tiles[j], self.tiles[i]

    def is_empty(self) -> bool:
        """Return True when no tile remains in the deck."""
        if not self.tiles:
            return True
        else:
            return False
