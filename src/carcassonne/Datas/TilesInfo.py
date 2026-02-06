
class TilesInfo:
    def __init__(self):
        self.tiles_count = {
            'FFFF/m': 4, 'FFFR/m': 2, 'CFFF': 5, 'FCFC/f': 3, 'CFCF/c': 1, 'CFCF/b': 2,
            'CCCC/b': 1, 'FFCC': 2, 'CCFF': 3, 'CCFF/b': 2, 'CCCF': 3, 'CCCF/b': 1, 'CCCR': 1, 'CCCR/b': 2, 'FRFR': 8,
            'FFRR': 9, 'CRFR': 4, 'CFRR': 3, 'CRRF': 3, 'CCRR': 3, 'CCRR/b': 2, 'FRRR': 4, 'CRRR': 3,
            'RRRR': 1, 'FSRS/m': 1, 'FFSF': 2, 'FSFS': 2, 'FFSS': 2, 'CSCS': 1, 'CCSS': 1,
            'CSRS': 1,'RSRS': 1, 'RRSS': 1
        }
        
        self.tiles_center = {
            'FFFF/m': 'm', 'FFFR/m': 'm', 'CFFF': 'F', 'FCFC/f': 'F', 'CFCF/c': 'C', 'CFCF/b': 'C',
            'CCCC/b': 'C', 'FFCC': 'F', 'CCFF': 'F', 'CCFF/b': 'F', 'CCCF': 'C', 'CCCF/b': 'C', 'CCCR': 'C', 'CCCR/b': 'C', 'FRFR': 'R',
            'FFRR': 'F', 'CRFR': 'R', 'CFRR': 'F', 'CRRF': 'F', 'CCRR': 'F', 'CCRR/b': 'F', 'FRRR': 'R', 'CRRR': 'R',
            'RRRR': 'R', 'FSRS/m': 'm', 'FFSF': 'S', 'FSFS': 'S', 'FFSS': 'F', 'CSCS': 'S', 'CCSS': 'F',
            'CSRS': 'R','RSRS': 'R', 'RRSS': 'F'
        }
        
        self.tiles_connections = {
            'FFFF/m': {'F' : [[0,1,2,3]]}, 'FFFR/m': {'F' : [[0,1,2]], 'R' : [[3]]}, 'CFFF': {'C' : [[0]], 'F' : [[1,2,3,4]]}, 
            'FCFC/f': {'F' : [[0,2,4]], 'C' : [[1], [3]]}, 'CFCF/c': {'C' : [[0,2,4]], 'F' : [[1],[3]]}, 'CFCF/b': {'C' : [[0,2,4]], 'F' : [[1],[3]]},
            'CCCC/b': {'C' : [[0,1,2,3,4]]}, 'FFCC': {'F' : [[0,1,4]], 'C' : [[2],[3]]}, 'CCFF': {'C' : [[0,1]], 'F' : [[2,3,4]]}, 
            'CCFF/b': {'C' : [[0,1]], 'F' : [[2,3,4]]}, 'CCCF': {'C' : [[0,1,2,4]], 'F' : [[3]]}, 'CCCF/b': {'C' : [[0,1,2,4]], 'F' : [[3]]}, 
            'CCCR': {'C' : [[0,1,2,4]], 'R' : [[3]]}, 'CCCR/b': {'C' : [[0,1,2,4]], 'R' : [[3]]}, 'FRFR': {'F' : [[0,[1,'N'],[3,'N']],[2,[1,'S'],[3,'S']]], 'R' : [[1,3,4]]},
            'FFRR': {'F' : [[0,1,[2,'E'],[3,'N'],4], [[2,'W'],[3,'S']]], 'R' : [[2,3]]}, 'CRFR': {'C' : [[0]], 'R' : [[1,3,4]], 'F' : [[[1,'S'],2,[3,'S']],[[1,'N'],[3,'N']]]}, 
            'CFRR': {'C' : [[0]], 'F' : [[1,[2,'E'],[3,'N'],4], [[2,'W'],[3,'S']]], 'R' : [[2,3]]}, 'CRRF': {'C' : [[0]], 'R' : [[1,2]], 'F' : [[[1,'N'],[2,'W'],3], [[1,'S'],[2,'E']]]}, 
            'CCRR': {'C' : [[0,1]], 'R' : [[2,3]], 'F': [[[2,'E'],[3,'N']], [[2,'W'],[3,'S']]]}, 'CCRR/b': {'C' : [[0,1]], 'R' : [[2,3]], 'F': [[[2,'E'],[3,'N']], [[2,'W'],[3,'S']]]}, 
            'FRRR': {'F' : [[0,[1,'N'],[3,'N']], [[1,'S'],[2,'E']], [[2,'W'],[3,'S']]], 'R' : [[1,2,3,4]]}, 
            'CRRR': {'C' : [[0]], 'F': [[[1,'N'],[3,'N']], [[1,'S'],[2,'E']], [[2,'W'],[3,'S']]], 'R' : [[1,2,3,4]]},
            'RRRR': {'R' : [[0,1,2,3,4]], 'F' : [[[0,'W'],[3,'N']], [[0,'E'],[1,'N']], [[2,'E'],[1,'S']], [[2,'W'],[3,'S']]]}, 
            'FSRS/m': {'F' : [[0,[1,'N'],[3,'N']], [[1,'S'],[2,'E']], [[2,'W'],[3,'S']]], 'S' : [[1,3]], 'R': [[2]]}, 'FFSF': {'F' : [[0,1,2,3]], 'S' : [[2,4]]}, 
            'FSFS': {'F' : [[0,[1,'N'],[3,'N']], [2,[1,'S'],[3,'S']]], 'S' : [[1,3]]}, 'FFSS': {'F' : [[0,1,[2,'E'],[3,'N']], [[2,'W'],[3,'S']]], 'S' : [[2,3]]}, 
            'CSCS': {'C' : [[0],[2]], 'S' : [[1,3]], 'F': [[[1,'N'],[3,'N']], [[1,'S'],[3,'S']]]}, 'CCSS': {'C' : [[0,1]], 'S' : [[2,3]], 'F': [[[2,'E'],[3,'N']], [[2,'W'],[3,'S']]]},
            'CSRS': {'C' : [[0]], 'S' : [[1,3]], 'R' : [[3,4]]},'RSRS': {'R' : [[0,2]], 'S' : [[1,3]]}, 
            'RRSS': {'R' : [[0,1]], 'S' : [[2,3]], 'F' : [[[0,'W'],[1,'S'],[2,'E'],[3,'N']], [[0,'E'],[1,'N']], [[2,'W'],[3,'S']]]}
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
