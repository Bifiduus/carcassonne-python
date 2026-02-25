"""This module defines the Meeple class, representing a player token placed on the board."""
from dataclasses import dataclass

# Position labels for the 9 positions on a tile (3x3 grid)
POSITION_LABELS = {
    7: 'NW', 0: 'N', 1: 'NE',
    6: 'W',  8: 'C', 2: 'E',
    5: 'SW', 4: 'S', 3: 'SE'
}


@dataclass
class Meeple:
    """Represents a meeple (player token) placed on the board."""
    player_id: int          # Name of the player who owns this meeple
    tile_id: int              # ID of the tile where the meeple is placed
    position: int             # Position on the tile (0-8)
    lands_components: str     # Name of the lands component (e.g., 'C1', 'F2', 'R1')

    def __init__(self, player_id: int, tile_id: int, position: int, lands_components: str):
        self.player_id = player_id
        self.tile_id = tile_id
        self.position = position
        self.lands_components = lands_components
        
    def __post_init__(self):
        """Validate position is within valid range."""
        if not 0 <= self.position <= 8:
            raise ValueError(f"Position must be between 0 and 8, got {self.position}")

    def get_position_label(self) -> str:
        """Get the label for this position (N, NE, E, SE, S, SW, W, NW, C)."""
        return POSITION_LABELS.get(self.position, 'UNKNOWN')

    def __repr__(self) -> str:
        pos_label = self.get_position_label()
        return f"Meeple(player={self.player_name}, tile={self.tile_id}, pos={pos_label}, lands_components={self.lands_components})"
