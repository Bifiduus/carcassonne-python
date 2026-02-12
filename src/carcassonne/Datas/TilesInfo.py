"""This module defines the TilesInfo class, which provides information about the different types of tiles in the Carcassonne game.
The TilesInfo class includes methods to check if a tile type is still available, to remove a tile from the available count, and to add a tile back to the available count. 
It also contains data structures that represent the sides of each tile type and the connections between those sides, which are essential for determining how tiles can be placed on the board and how they interact with each other.
"""
from carcassonne.BusinessLogic.Interfaces.ITilesInfo import ITilesInfo

class Tile:
    code : str

    matrix : list[list[str]]

    # Direction matrices indexed by orientation (0, 1, 2, 3)
    direction_matrix = [
        # 0 rotation
        [['NW', 'N', 'NE'],
         ['W',  'C', 'E'],
         ['SW', 'S', 'SE']],
        # 1 rotation (90° clockwise)
        [['SW', 'W', 'NW'],
         ['S',  'C', 'N'],
         ['SE', 'E', 'NE']],
        # 2 rotations (180° clockwise)
        [['SE', 'S', 'SW'],
         ['E',  'C', 'W'],
         ['NE', 'N', 'NW']],
        # 3 rotations (270° clockwise)
        [['NE', 'E', 'SE'],
         ['N',  'C', 'S'],
         ['NW', 'W', 'SW']]
    ]

    def __init__(self, code: str):
        self.code = code

        self.matrix = TilesInfo.tiles_sides[code]

class TilesInfo(ITilesInfo):
    def __init__(self):
        self.tiles_dict = {
            # Basic Tiles
            'FFFF': ['m'], 'FFFR': ['m'], 'CFFF': ['void'], 'FCFC': ['f'], 'CFCF': ['c', 'b'],
            'CCCC': ['b'], 'FFCC': ['void'], 'CCFF': ['void', 'b'], 'CCCF': ['void', 'b'], 'CCCR': ['void', 'b'], 'FRFR': ['void'],
            'FFRR': ['void'], 'CRFR': ['void'], 'CFRR': ['void'], 'CRRF': ['void'],
            'CCRR': ['void', 'b'], 'FRRR': ['void'], 'CRRR': ['void'], 'RRRR': ['void'],

            # 'The River' Expansion
            'FSRS': ['m'], 'FFSF': ['void'], 'FSFS': ['void'], 'FFSS': ['void'], 'CSCS': ['void'], 'CCSS': ['void'],
            'CSRS': ['void'],'RSRS': ['void'], 'RRSS': ['void']
        }

        self.direction_list = ['N', 'E', 'S', 'W']

        self.direction_dict = {'N': 0, 'E': 1, 'S': 2, 'W': 3}

        self.tiles_count = {
            # Basic Tiles
            'FFFF/m': 4, 'FFFR/m': 2, 'CFFF': 5, 'FCFC/f': 3, 'CFCF/c': 1, 'CFCF/b': 2,
            'CCCC/b': 1, 'FFCC': 2, 'CCFF': 3, 'CCFF/b': 2, 'CCCF': 3, 'CCCF/b': 1,
            'CCCR': 1, 'CCCR/b': 2, 'FRFR': 8, 'FFRR': 9, 'CRFR': 4, 'CFRR': 3, 'CRRF': 3,
            'CCRR': 3, 'CCRR/b': 2, 'FRRR': 4, 'CRRR': 3, 'RRRR': 1,

            # 'The River' Expansion
            'FSRS/m': 1, 'FFSF': 2, 'FSFS': 2, 'FFSS': 2, 'CSCS': 1, 'CCSS': 1,
            'CSRS': 1,'RSRS': 1, 'RRSS': 1
        }

        self.tiles_connections = {
            # Basic Tiles
            'FFFF/m': {'M' : [['C']], 'F' : [['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']]},
            'FFFR/m': {'M' : [['C']], 'F' : [['N', 'NE', 'E', 'SE', 'S', 'SW', 'NW']], 'R' : [['W']]},
            'CFFF': {'C' : [['N']], 'F' : [['NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'C']]},
            'FCFC/f': {'C' : [['E'], ['W']], 'F' : [['N', 'NE', 'SE', 'S', 'SW', 'NW', 'C']]},
            'CFCF/c': { 'C' : [['N', 'S', 'C']], 'F' : [['NE', 'E', 'SE'], ['SW', 'W', 'NW']]},
            'CFCF/b': { 'C' : [['N', 'S', 'C']], 'F' : [['NE', 'E', 'SE'], ['SW', 'W', 'NW']]},

            'CCCC/b': {'C' : [['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW', 'C']]},
            'FFCC': {'C' : [['S'], ['W']], 'F' : [['N', 'NE', 'E', 'SW', 'SE', 'C']]},
            'CCFF': {'C' : [['N', 'NE', 'E']], 'F' : [['SE', 'S', 'SW', 'W', 'NW', 'C']]},
            'CCFF/b': {'C' : [['N', 'NE', 'E']], 'F' : [['SE', 'S', 'SW', 'W', 'NW', 'C']]},
            'CCCF': {'C' : [['N', 'NE', 'E', 'SE', 'S', 'C']], 'F' : [['SW', 'W', 'NW']]},
            'CCCF/b': {'C' : [['N', 'NE', 'E', 'SE', 'S', 'C']], 'F' : [['SW', 'W', 'NW']]},

            'CCCR': {'C' : [['N', 'NE', 'E', 'SE', 'S', 'C']], 'F' : [['SW'], ['NW']], 'R' : [['W']]},
            'CCCR/b': {'C' : [['N', 'NE', 'E', 'SE', 'S', 'C']], 'F' : [['SW'], ['NW']], 'R' : [['W']]},
            'FRFR': {'F' : [['N', 'NE', 'NW'], ['SE', 'S', 'SW']], 'R' : [['E', 'W', 'C']]},
            'FFRR': {'F' : [['N', 'NE', 'E', 'SE', 'NW', 'C'], ['SW']], 'R' : [['S', 'W']]},
            'CRFR': {'C' : [['N']], 'F' : [['NE', 'NW'], ['SE', 'S', 'SW']], 'R' : [['E', 'W', 'C']]},
            'CFRR': {'C' : [['N']], 'F' : [['NE', 'E', 'SE', 'NW', 'C'], ['SW']], 'R' : [['S', 'W']]},
            'CRRF': {'C' : [['N']], 'F' : [['NE', 'SW', 'W', 'NW', 'C'], ['SE']], 'R' : [['E', 'S']]},

            'CCRR': {'C' : [['N', 'NE', 'E']], 'F': [['SE', 'NW', 'C'], ['SW']], 'R' : [['S', 'W']]},
            'CCRR/b': {'C' : [['N', 'NE', 'E']], 'F': [['SE', 'NW', 'C'], ['SW']], 'R' : [['S', 'W']]},
            'FRRR': {'F' : [['N', 'NE', 'NW'], ['SE'], ['SW']], 'R' : [['E', 'S', 'W', 'C']]},
            'CRRR': {'C' : [['N']], 'F' : [['NE', 'NW'], ['SE'], ['SW']], 'R' : [['E', 'S', 'W', 'C']]},
            'RRRR': {'F' : [['NE'], ['NW'], ['SE'], ['SW']], 'R' : [['N', 'E', 'S', 'W', 'C']]},

            # 'The River' Expansion
            'FSRS/m': {'M' : [['C']], 'F' : [['N', 'NE', 'NW'], ['SE'], ['SW']], 'R': [['S']], 'S' : [['E', 'W']]},
            'FFSF': {'F' : [['N', 'NE', 'E', 'SE', 'SW', 'W', 'NW']], 'S' : [['S', 'C']]},
            'FSFS': {'F' : [['N', 'NE', 'NW'], ['SE', 'S', 'SW']], 'S' : [['E', 'W', 'C']]},
            'FFSS': {'F' : [['N', 'NE', 'E', 'SE', 'NW', 'C'], ['SW']], 'S' : [['S', 'W']]},
            'CSCS': {'C' : [['N'], ['S']], 'F': [['NE', 'NW'], ['SE', 'SW']], 'S' : [['E', 'W', 'C']]},
            'CCSS': {'C' : [['N', 'NE', 'E']], 'F': [['SE', 'NW', 'C'], ['SW']], 'S' : [['S', 'W']]},

            'CSRS': {'C' : [['N']], 'F': [['NE'], ['SE'], ['SW'], ['NW']], 'R' : [['S', 'C']], 'S' : [['E', 'W']],},
            'RSRS': {'F': [['NE'], ['SE'], ['SW'], ['NW']], 'R' : [['N', 'S', 'C']], 'S' : [['E', 'W']],},
            'RRSS': {'F' : [['NE'], ['SE', 'NW', 'C'], ['SW']], 'R' : [['N', 'E']], 'S' : [['S', 'W']]}
        }

    def is_tile_left(self, tile_code: str) -> bool:
        """
        Checks if there are tiles left of the specified type in the game.

        Returns True if there are tiles left, False otherwise.
        """
        if self.tiles_count.get(tile_code, 0) > 0:
            return True
        return False

    def remove_tile(self, tile_code: str) -> None:
        """
        Decreases the count of the specified tile type by one.

        Raises a ValueError if there are no tiles left of that type.
        """
        if self.tiles_count.get(tile_code, 0) <= 0:
            raise ValueError(f"No tiles left of type: {tile_code}")
        self.tiles_count[tile_code] -= 1

    def add_tile(self, tile_code: str) -> None:
        """
        Increases the count of the specified tile type by one.
        """
        if tile_code not in self.tiles_count:
            raise ValueError(f"Invalid tile code: {tile_code}")
        self.tiles_count[tile_code] += 1
