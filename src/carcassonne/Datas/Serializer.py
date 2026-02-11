"""This module defines the Serializer class, which provides methods for parsing move strings and building move strings from move records in the Carcassonne game. 
The Serializer class includes the parse_move function, which takes a move string and extracts the relevant information such as tile sides, target vertex, rotation, and meeple placement. 
It also includes the build_str function, which takes a MoveRecord object and constructs a move string that can be used to represent the move in the game history.
"""
import re


PLACEMENT_RE = re.compile(r"^(?P<target>\d+)(?P<side>[NESW])(?P<rot>[0-3])$")
MEEPLE_SET = {"N", "E", "S", "W"}



def parse_move(move):
    if not isinstance(move, str):
        raise ValueError("move must be a string")

    parts = move.split("/")
    if len(parts) < 2:
        raise ValueError("move must contain at least tile and placement")

    tile_sides = parts[0]

    if len(tile_sides) != 4:
        raise ValueError("tile must have 4 sides")

    center = None
    placement_index = 1
    if len(parts) >= 3 and len(parts[1]) == 1 and not PLACEMENT_RE.match(parts[1]):
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
    meeple = None
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


def build_str(record):
    placement = f"{record.target_id}{record.target_side}{record.rotation}"
    tile_part = record.tile_sides
    if record.center:
        tile_part = f"{tile_part}/{record.center}"
    if record.meeple:
        return f"{record.player_id}:{tile_part}/{placement}/{record.meeple};"
    return f"{record.player_id}:{tile_part}/{placement};"
