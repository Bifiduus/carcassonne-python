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

    placement_index = None
    for idx in range(1, len(parts)):
        if PLACEMENT_RE.match(parts[idx]):
            placement_index = idx
            break
    if placement_index is None:
        raise ValueError("invalid placement format")

    placement = parts[placement_index]
    match = PLACEMENT_RE.match(placement)

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

    return {
        "tile_sides": tile_sides,
        "target_id": target_id,
        "target_side": target_side,
        "rotation": rotation,
        "meeple": meeple,
    }

