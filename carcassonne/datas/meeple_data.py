"""Meeple model representing a player token placed on the board."""

from dataclasses import dataclass
from typing import Final

# Position labels for the 9 positions on a tile (3x3 grid)
POSITION_LABELS: Final[dict[int, str]] = {
    7: "NW",
    0: "N",
    1: "NE",
    6: "W",
    8: "C",
    2: "E",
    5: "SW",
    4: "S",
    3: "SE",
}
MIN_POSITION: Final[int] = 0
MAX_POSITION: Final[int] = 8


@dataclass
class Meeple:
    """Represents a meeple (player token) placed on the board."""

    player_id: int
    tile_id: int
    position: int

    # Name of the lands component (e.g., 'C1', 'F2', 'R1')
    lands_components: str

    def __post_init__(self) -> None:
        """Validates that the meeple position stays within the allowed
        range for a 3x3 tile."""
        if self.player_id < 0:
            raise ValueError(
                f"player_id must be >= 0, got {self.player_id}"
            )

        if self.tile_id < 0:
            raise ValueError(f"tile_id must be >= 0, got {self.tile_id}")

        if not MIN_POSITION <= self.position <= MAX_POSITION:
            raise ValueError(
                f"Position must be between {MIN_POSITION} and "
                f"{MAX_POSITION}, got {self.position}"
            )

    def get_position_label(self) -> str:
        """Converts the numeric position index into a readable cardinal
        label (N, NE, E, SE, S, SW, W, NW, C).

        Args:
            None.

        Returns:
            str: The label corresponding to the current position.
        """
        return POSITION_LABELS.get(self.position, "UNKNOWN")

    def __repr__(self) -> str:
        """Builds a compact textual representation of the meeple,
        useful for debugging and logs.

        Args:
            None.

        Returns:
            str: A string representing the current meeple state.
        """
        pos_label: str = self.get_position_label()
        return (
            "Meeple("
            f"player={self.player_id}, "
            f"tile={self.tile_id}, "
            f"pos={pos_label}, "
            f"lands_components={self.lands_components}"
            ")"
        )
