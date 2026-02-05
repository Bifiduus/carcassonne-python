
class TilesCount:
    def __init__(self):
        self.tiles_count = {
            'FFFF/m': 4, 'FFFR/m': 2, 'CFFF': 5, 'FCFC': 3, 'CFCF/c': 1, 'CFCF/b': 2,
            'CCCC/b': 1, 'FFCC': 2, 'CCFF': 3, 'CCFF/b': 2, 'CCCF': 3, 'CCCF/b': 1, 'CCCR': 1, 'CCCR/b': 2, 'FRFR': 8,
            'FFRR': 9, 'CRFR': 4, 'CFRR': 3, 'CRRF': 3, 'CCRR': 3, 'CCRR/b': 2, 'FRRR': 4, 'CRRR': 3,
            'RRRR': 1, 'FSRS/m': 1, 'FFSF': 2, 'FSFS': 2, 'FFSS': 2, 'CSCS': 1, 'CCSS': 1,
            'CSRS': 1,'RSRS': 1, 'RRSS': 1
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
