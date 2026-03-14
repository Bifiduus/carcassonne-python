"""
This module defines helper functions for move string serialization.
It parses move commands into structured data and builds printable history lines.
"""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from carcassonne.Datas.History import MoveRecord

# Placement format: <target_vertex_id><side><rotation>, e.g. "12N3".
PLACEMENT_RE: re.Pattern[str] = re.compile(r"^(?P<target>\d+)(?P<side>[NESW])(?P<rot>[0-3])$")
# Allowed meeple placement sides in the move format.
MEEPLE_SET: set[str] = {"N", "E", "S", "W"}


def parse_move(move: str) -> dict:
    """
    Parse a raw move string into a structured dictionary.

    Args:
        move: Move string such as "CFFF/10N1/E"

    Returns:
        Dictionary with tile, center, placement, rotation, and meeple data

    Raises:
        ValueError: If the move format is invalid
    """
    if not isinstance(move, str):
        raise ValueError("move must be a string")

    parts: list[str] = move.split("/")
    if len(parts) < 2:
        raise ValueError("move must contain at least tile and placement")

    tile_sides: str = parts[0]

    if len(tile_sides) != 4:
        raise ValueError("tile must have 4 sides")

    center = None
    placement_index = 1
    # Some tiles include an explicit center part before placement.
    if len(parts) >= 3 and len(parts[1]) == 1 and not PLACEMENT_RE.match(parts[1]):
        center: str = parts[1]
        placement_index = 2
    if placement_index >= len(parts):
        raise ValueError("invalid placement format")

    placement: str = parts[placement_index]
    match: re.Match[str] | None = PLACEMENT_RE.match(placement)
    if not match:
        raise ValueError("invalid placement format")

    target_id = int(match.group("target"))
    target_side: str | re.Any = match.group("side")
    rotation = int(match.group("rot"))
    meeple = None
    if placement_index + 1 < len(parts):
        candidate: str = parts[placement_index + 1]
        # Meeple position is optional but must be one of the cardinal sides.
        if candidate in MEEPLE_SET:
            meeple: str = candidate
        else:
            raise ValueError("invalid meeple format")
    if placement_index + 2 < len(parts):
        raise ValueError("too many parts in move")

    return {
        "tile_sides": tile_sides,
        "center": center,
        "target_id": target_id,
        "target_side": target_side,
        "rotation": rotation,
        "meeple": meeple,
    }


def build_str(record: "MoveRecord") -> str:
    """
    Build a standardized history string from a move record.

    Args:
        record: Move record containing player id and move string

    Returns:
        Serialized history entry with trailing ';'
    """
    return f"{record.player_id}:{record.move_str.strip(';')};"
