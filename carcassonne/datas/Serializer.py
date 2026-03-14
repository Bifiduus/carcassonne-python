"""This module defines the Serializer class, which provides methods for parsing move strings and building move strings from move records in the Carcassonne game. 
The Serializer class includes the parse_move function, which takes a move string and extracts the relevant information such as tile sides, target vertex, rotation, and meeple placement. 
It also includes the build_str function, which takes a MoveRecord object and constructs a move string that can be used to represent the move in the game history.
"""
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from carcassonne.datas.History import MoveRecord

PLACEMENT_RE: re.Pattern[str] = re.compile(r"^(?P<target>\d+)(?P<side>[NESW])(?P<rot>[0-3])$")
MEEPLE_SET: set[str] = {"N", "E", "S", "W"}

def parse_move(move: str) -> dict:
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
    return f"{record.player_id}:{record.move_str.strip(';')};"
