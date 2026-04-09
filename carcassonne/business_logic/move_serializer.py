"""Business-logic level move parsing and formatting helpers."""

import re
from typing import Any


PLACEMENT_RE: re.Pattern[str] = re.compile(
    r"^(?P<target>\d+)(?P<side>[NESW])(?P<rot>[0-3])$"
)
# Valid meeple placement labels used by move parser/validator.
MEEPLE_SET: set[str] = {
    "N",
    "NE",
    "E",
    "SE",
    "S",
    "SW",
    "W",
    "NW",
    "C",
}


def parse_move(move: str) -> dict:
    """Parse a move string into structured fields.

    Supported formats:
    - ``TILE/TARGETSIDE_ROT``               (no center, no meeple)
    - ``TILE/CENTER/TARGETSIDE_ROT``        (center tile type)
    - each of the above + ``/MEEPLE_POS``   (optional meeple placement)

    Returns:
        A dict containing tile_sides, center, target_id, target_side,
        rotation, and meeple.

    Raises:
        ValueError: If the move format is invalid.
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
    if (
        len(parts) >= 3
        and len(parts[1]) == 1
        and not PLACEMENT_RE.match(parts[1])
    ):
        center = parts[1]
        placement_index = 2

    if placement_index >= len(parts):
        raise ValueError("invalid placement format")

    placement = parts[placement_index]
    match = PLACEMENT_RE.match(placement)
    if not match:
        raise ValueError("invalid placement format")

    target_id = int(match.group("target"))
    target_side = match.group("side")
    rotation = int(match.group("rot"))

    meeple = ""
    if placement_index + 1 < len(parts):
        candidate = parts[placement_index + 1]
        if candidate in MEEPLE_SET:
            meeple = candidate
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


def build_str(record: Any) -> str:
    """Build the history serialization form ``player_id:move;``."""
    return f"{record.player_id}:{record.move_str.strip(';')};"
