"""Tile definitions and availability metadata for Carcassonne.

This module provides tile-side data, connectivity rules, and counters used to
draw, place, and restore tiles during gameplay.
"""

from carcassonne.business_logic.interfaces.i_tiles_info import ITilesInfo


class Tile:
    code: str

    # Direction matrices indexed by orientation (0, 1, 2, 3)
    direction_matrix = [
        # 0 rotation
        [["NW", "N", "NE"], ["W", "C", "E"], ["SW", "S", "SE"]],
        # 1 rotation (90° clockwise)
        [["SW", "W", "NW"], ["S", "C", "N"], ["SE", "E", "NE"]],
        # 2 rotations (180° clockwise)
        [["SE", "S", "SW"], ["E", "C", "W"], ["NE", "N", "NW"]],
        # 3 rotations (270° clockwise)
        [["NE", "E", "SE"], ["N", "C", "S"], ["NW", "W", "SW"]],
    ]

    def __init__(
        self,
        code: str,
        connections: dict | None = None,
        connect_to: dict | None = None,
    ) -> None:
        self.code = code
        # tiles_lands is the terrain definitions for this tile
        self.tiles_lands = connections if connections is not None else {}
        self.connect_to = connect_to if connect_to is not None else {}


class TilesInfo(ITilesInfo):
    def __init__(self) -> None:
        self.tiles_dict = {
            # Basic Tiles
            "FFFF": ["m"],
            "FFFR": ["m"],
            "CFFF": ["void"],
            "FCFC": ["f"],
            "CFCF": ["c", "b"],
            "CCCC": ["b"],
            "FFCC": ["void"],
            "CCFF": ["void", "b"],
            "CCCF": ["void", "b"],
            "CCCR": ["void", "b"],
            "FRFR": ["void"],
            "FFRR": ["void"],
            "CRFR": ["void"],
            "CFRR": ["void"],
            "CRRF": ["void"],
            "CCRR": ["void", "b"],
            "FRRR": ["void"],
            "CRRR": ["void"],
            "RRRR": ["void"],
            # 'The River' Expansion
            "FSRS": ["m"],
            "FFSF": ["void"],
            "FSFS": ["void"],
            "FFSS": ["void"],
            "CSCS": ["void"],
            "CCSS": ["void"],
            "CSRS": ["void"],
            "RSRS": ["void"],
            "RRSS": ["void"],
        }

        self.tiles_parts_list = [
            "NW",
            "N",
            "NE",
            "E",
            "SE",
            "S",
            "SW",
            "W",
            "C",
        ]
        self.direction_list = ["N", "E", "S", "W"]

        self.meeple_placement_list = [
            "N",
            "NE",
            "E",
            "SE",
            "S",
            "SW",
            "W",
            "NW",
            "C",
        ]

        self.direction_dict = {"N": 0, "E": 1, "S": 2, "W": 3}

        self.direction_matrix = [
            ["NW", "N", "NE"],
            ["W", "C", "E"],
            ["SW", "S", "SE"],
        ]

        self.matrix_coordinates = {
            "NW": (0, 0),
            "N": (0, 1),
            "NE": (0, 2),
            "E": (1, 2),
            "SE": (2, 2),
            "S": (2, 1),
            "SW": (2, 0),
            "W": (1, 0),
            "C": (1, 1),
        }

        self.tiles_count = {
            # Basic Tiles
            "FFFF/m": 4,
            "FFFR/m": 2,
            "CFFF": 5,
            "FCFC/f": 3,
            "CFCF/c": 1,
            "CFCF/b": 2,
            "CCCC/b": 1,
            "FFCC": 2,
            "CCFF": 3,
            "CCFF/b": 2,
            "CCCF": 3,
            "CCCF/b": 1,
            "CCCR": 1,
            "CCCR/b": 2,
            "FRFR": 8,
            "FFRR": 9,
            "CRFR": 4,
            "CFRR": 3,
            "CRRF": 3,
            "CCRR": 3,
            "CCRR/b": 2,
            "FRRR": 4,
            "CRRR": 3,
            "RRRR": 1,
            # 'The River' Expansion
            "FSRS/m": 1,
            "FFSF": 1,
            "FSFS": 2,
            "FFSS": 2,
            "CSCS": 1,
            "CCSS": 1,
            "CSRS": 1,
            "RSRS": 1,
            "RRSS": 1,
        }

        self.tiles_lands = {
            # Basic Tiles
            "FFFF/m": {
                "M": [["C"]],
                "F": [["N", "NE", "E", "SE", "S", "SW", "W", "NW"]],
            },
            "FFFR/m": {
                "M": [["C"]],
                "F": [["N", "NE", "E", "SE", "S", "SW", "NW"]],
                "R": [["W"]],
            },
            "CFFF": {
                "C": [["N"]],
                "F": [["NE", "E", "SE", "S", "SW", "W", "NW", "C"]],
            },
            "FCFC/f": {
                "C": [["E"], ["W"]],
                "F": [["N", "NE", "SE", "S", "SW", "NW", "C"]],
            },
            "CFCF/c": {
                "C": [["N", "S", "C"]],
                "F": [["NE", "E", "SE"], ["SW", "W", "NW"]],
            },
            "CFCF/b": {
                "C": [["N", "S", "C"]],
                "F": [["NE", "E", "SE"], ["SW", "W", "NW"]],
            },
            "CCCC/b": {
                "C": [["N", "NE", "E", "SE", "S", "SW", "W", "NW", "C"]]
            },
            "FFCC": {
                "C": [["S"], ["W"]],
                "F": [["N", "NE", "E", "SW", "SE", "C"]],
            },
            "CCFF": {
                "C": [["N", "NE", "E"]],
                "F": [["SE", "S", "SW", "W", "NW", "C"]],
            },
            "CCFF/b": {
                "C": [["N", "NE", "E"]],
                "F": [["SE", "S", "SW", "W", "NW", "C"]],
            },
            "CCCF": {
                "C": [["N", "NE", "E", "SE", "S", "C"]],
                "F": [["SW", "W", "NW"]],
            },
            "CCCF/b": {
                "C": [["N", "NE", "E", "SE", "S", "C"]],
                "F": [["SW", "W", "NW"]],
            },
            "CCCR": {
                "C": [["N", "NE", "E", "SE", "S", "C"]],
                "F": [["SW"], ["NW"]],
                "R": [["W"]],
            },
            "CCCR/b": {
                "C": [["N", "NE", "E", "SE", "S", "C"]],
                "F": [["SW"], ["NW"]],
                "R": [["W"]],
            },
            "FRFR": {
                "F": [["N", "NE", "NW"], ["SE", "S", "SW"]],
                "R": [["E", "W", "C"]],
            },
            "FFRR": {
                "F": [["N", "NE", "E", "SE", "NW", "C"], ["SW"]],
                "R": [["S", "W"]],
            },
            "CRFR": {
                "C": [["N"]],
                "F": [["NE", "NW"], ["SE", "S", "SW"]],
                "R": [["E", "W", "C"]],
            },
            "CFRR": {
                "C": [["N"]],
                "F": [["NE", "E", "SE", "NW", "C"], ["SW"]],
                "R": [["S", "W"]],
            },
            "CRRF": {
                "C": [["N"]],
                "F": [["NE", "SW", "W", "NW", "C"], ["SE"]],
                "R": [["E", "S"]],
            },
            "CCRR": {
                "C": [["N", "NE", "E"]],
                "F": [["SE", "NW", "C"], ["SW"]],
                "R": [["S", "W"]],
            },
            "CCRR/b": {
                "C": [["N", "NE", "E"]],
                "F": [["SE", "NW", "C"], ["SW"]],
                "R": [["S", "W"]],
            },
            # For now Center is nothing because it isn't a land, it splits the
            # roads
            "FRRR": {
                "F": [["N", "NE", "NW"], ["SE"], ["SW"]],
                "R": [["E"], ["S"], ["W"]],
            },
            # For now Center is nothing because it isn't a land, it splits the
            # roads
            "CRRR": {
                "C": [["N"]],
                "F": [["NE", "NW"], ["SE"], ["SW"]],
                "R": [["E"], ["S"], ["W"]],
            },
            # For now Center is nothing because it isn't a land, it splits the
            # roads
            "RRRR": {
                "F": [["NE"], ["NW"], ["SE"], ["SW"]],
                "R": [["N"], ["E"], ["S"], ["W"]],
            },
            # 'The River' Expansion
            "FSRS/m": {
                "M": [["C"]],
                "F": [["N", "NE", "NW"], ["SE"], ["SW"]],
                "R": [["S"]],
                "S": [["E", "W"]],
            },
            "FFSF": {
                "F": [["N", "NE", "E", "SE", "SW", "W", "NW"]],
                "S": [["S", "C"]],
            },
            "FSFS": {
                "F": [["N", "NE", "NW"], ["SE", "S", "SW"]],
                "S": [["E", "W", "C"]],
            },
            "FFSS": {
                "F": [["N", "NE", "E", "SE", "NW", "C"], ["SW"]],
                "S": [["S", "W"]],
            },
            "CSCS": {
                "C": [["N"], ["S"]],
                "F": [["NE", "NW"], ["SE", "SW"]],
                "S": [["E", "W", "C"]],
            },
            "CCSS": {
                "C": [["N", "NE", "E"]],
                "F": [["SE", "NW", "C"], ["SW"]],
                "S": [["S", "W"]],
            },
            "CSRS": {
                "C": [["N"]],
                "F": [["NE"], ["SE"], ["SW"], ["NW"]],
                "R": [["S", "C"]],
                "S": [["E", "W"]],
            },
            "RSRS": {
                "F": [["NE"], ["SE"], ["SW"], ["NW"]],
                "R": [["N", "S", "C"]],
                "S": [["E", "W"]],
            },
            "RRSS": {
                "F": [["NE"], ["SE", "NW", "C"], ["SW"]],
                "R": [["N", "E"]],
                "S": [["S", "W"]],
            },
        }

        self.connects_to = {
            # Basic Tiles
            "FFFF/m": {},
            "FFFR/m": {},
            "CFFF": {"NW": ["C", "F"], "NE": ["C", "F"]},
            "FCFC/f": {
                "NW": ["F", "C"],
                "NE": ["F", "C"],
                "SW": ["F", "C"],
                "SE": ["F", "C"],
            },
            "CFCF/c": {
                "NW": ["C", "F"],
                "NE": ["C", "F"],
                "SW": ["C", "F"],
                "SE": ["C", "F"],
            },
            "CFCF/b": {
                "NW": ["C", "F"],
                "NE": ["C", "F"],
                "SW": ["C", "F"],
                "SE": ["C", "F"],
            },
            "CCCC/b": {},
            "FFCC": {"NW": ["F", "C"], "SW": ["C", "C"], "SE": ["C", "F"]},
            "CCFF": {"NW": ["C", "F"], "SE": ["F", "C"]},
            "CCFF/b": {"NW": ["C", "F"], "SE": ["F", "C"]},
            "CCCF": {"NW": ["C", "F"], "SW": ["C", "F"]},
            "CCCF/b": {"NW": ["C", "F"], "SW": ["C", "F"]},
            "CCCR": {"NW": ["C", "F"], "SW": ["C", "F"]},
            "CCCR/b": {"NW": ["C", "F"], "SW": ["C", "F"]},
            "FRFR": {},
            "FFRR": {},
            "CRFR": {"NW": ["C", "F"], "NE": ["C", "F"]},
            "CFRR": {"NW": ["C", "F"], "NE": ["C", "F"]},
            "CRRF": {"NW": ["C", "F"], "NE": ["C", "F"]},
            "CCRR": {"NW": ["C", "F"], "SE": ["F", "C"]},
            "CCRR/b": {"NW": ["C", "F"], "SE": ["F", "C"]},
            "FRRR": {},
            "CRRR": {"NW": ["C", "F"], "NE": ["C", "F"]},
            "RRRR": {},
            # 'The River' Expansion
            "FSRS/m": {},
            "FFSF": {},
            "FSFS": {},
            "FFSS": {},
            "CSCS": {
                "NW": ["C", "F"],
                "NE": ["C", "F"],
                "SW": ["C", "F"],
                "SE": ["C", "F"],
            },
            "CCSS": {"NW": ["C", "F"], "SE": ["F", "C"]},
            "CSRS": {"NW": ["C", "F"], "NE": ["C", "F"]},
            "RSRS": {},
            "RRSS": {},
        }

        # Initialize Tile objects indexed by base code, with their connections
        self.tiles = {}
        seen_base_codes = set()
        for tile_code in sorted(self.tiles_lands.keys()):
            base_code = tile_code.split("/")[0]
            if base_code not in seen_base_codes:
                self.tiles[base_code] = Tile(
                    base_code,
                    self.tiles_lands[tile_code],
                    self.connects_to[tile_code],
                )
                seen_base_codes.add(base_code)

    def rotate_matrix_90(self, matrix: list[list[str]]) -> list[list[str]]:
        """
        Rotates a matrix 90 degrees clockwise.

        Args:
            matrix: A 2D list to rotate

        Returns:
            A new matrix rotated 90 degrees clockwise
        """
        n = len(matrix)
        m = len(matrix[0]) if matrix else 0

        # Create new matrix with swapped dimensions
        rotated = [["" for _ in range(n)] for _ in range(m)]

        for i in range(n):
            for j in range(m):
                rotated[j][n - 1 - i] = matrix[i][j]

        return rotated

    def is_tile_left(self, tile_code: str) -> bool:
        """
        Checks if there are tiles left of the specified type in the game.

        Returns True if there are tiles left, False otherwise.
        """
        if self.tiles_count.get(tile_code, 0) > 0:
            return True
        return False

    def add_tile(self, tile_code: str) -> None:
        """
        Increases the count of the specified tile type by one.
        """
        if tile_code not in self.tiles_count:
            raise ValueError(f"Invalid tile code: {tile_code}")
        self.tiles_count[tile_code] += 1

    def remove_tile(self, tile_code: str) -> None:
        """
        Decreases the count of the specified tile type by one.

        Raises a ValueError if there are no tiles left of that type.
        """
        if self.tiles_count.get(tile_code, 0) <= 0:
            raise ValueError(f"No tiles left of type: {tile_code}")
        self.tiles_count[tile_code] -= 1
