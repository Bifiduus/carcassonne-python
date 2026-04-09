"""Tile constants exposed at business_logic level."""

CARDINALS = ("N", "E", "S", "W")

OPPOSITE_CARDINAL = {
    "N": "S",
    "E": "W",
    "S": "N",
    "W": "E",
}

NORTH_DIR = 0
EAST_DIR = 1
SOUTH_DIR = 2
WEST_DIR = 3

DIRECTION_MAP = {
    "N": NORTH_DIR,
    "E": EAST_DIR,
    "S": SOUTH_DIR,
    "W": WEST_DIR,
}

# 3x3 matrix coordinates used to reference tile cells/edges/corners.
NORTHWEST_MATRIX = (0, 0)
NORTH_MATRIX = (0, 1)
NORTHEAST_MATRIX = (0, 2)
WEST_MATRIX = (1, 0)
CENTER_MATRIX = (1, 1)
EAST_MATRIX = (1, 2)
SOUTHWEST_MATRIX = (2, 0)
SOUTH_MATRIX = (2, 1)
SOUTHEAST_MATRIX = (2, 2)

# Mapping from meeple placement labels to 3x3 matrix positions.
MATCH_MATRIX = {
    "NW": NORTHWEST_MATRIX,
    "N": NORTH_MATRIX,
    "NE": NORTHEAST_MATRIX,
    "W": WEST_MATRIX,
    "C": CENTER_MATRIX,
    "E": EAST_MATRIX,
    "SW": SOUTHWEST_MATRIX,
    "S": SOUTH_MATRIX,
    "SE": SOUTHEAST_MATRIX,
}

# For each board-side index (N/E/S/W), gives the opposite matrix position.
OPPOSITE_SIDE_MATRIX = {
    0: SOUTH_MATRIX,
    1: WEST_MATRIX,
    2: NORTH_MATRIX,
    3: EAST_MATRIX,
}
