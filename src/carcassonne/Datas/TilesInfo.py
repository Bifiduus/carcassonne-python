from carcassonne.BusinessLogic.Interfaces.ITilesInfo import ITilesInfo

class Tile:
    code : str
    
    matrix : list[list[str]]
    
    direction_matrix = [['NW', 'N', 'NE'], 
                        ['W', 'C', 'E'], 
                        ['SW', 'S', 'SE']]
    
    def __init__(self, code: str):
        self.code = code
        
        self.matrix = TilesInfo.tiles_sides[code]

class TilesInfo(ITilesInfo):
    def __init__(self):
        self.tiles_dict = {
            'FFFF': ['m'], 'FFFR': ['m'], 'CFFF': ['void'], 'FCFC': ['f'], 'CFCF': ['c', 'b'],
            'CCCC': ['b'], 'FFCC': ['void'], 'CCFF': ['void', 'b'], 'CCCF': ['void', 'b'], 'CCCR': ['void', 'b'], 'FRFR': ['void'],
            'FFRR': ['void'], 'CRFR': ['void'], 'CFRR': ['void'], 'CRRF': ['void'], 'CCRR': ['void', 'b'], 'FRRR': ['void'], 'CRRR': ['void'],
            'RRRR': ['void'], 'FSRS': ['m'], 'FFSF': ['void'], 'FSFS': ['void'], 'FFSS': ['void'], 'CSCS': ['void'], 'CCSS': ['void'],
            'CSRS': ['void'],'RSRS': ['void'], 'RRSS': ['void']
        }

        self.direction_list = ['N', 'E', 'S', 'W']
        self.direction_dict = {'N': 0, 'E': 1, 'S': 2, 'W': 3}
        
        self.tiles_count = {
            'FFFF/m': 4, 'FFFR/m': 2, 'CFFF': 5, 'FCFC/f': 3, 'CFCF/c': 1, 'CFCF/b': 2,
            'CCCC/b': 1, 'FFCC': 2, 'CCFF': 3, 'CCFF/b': 2, 'CCCF': 3, 'CCCF/b': 1, 'CCCR': 1, 'CCCR/b': 2, 'FRFR': 8,
            'FFRR': 9, 'CRFR': 4, 'CFRR': 3, 'CRRF': 3, 'CCRR': 3, 'CCRR/b': 2, 'FRRR': 4, 'CRRR': 3,
            'RRRR': 1, 'FSRS/m': 1, 'FFSF': 2, 'FSFS': 2, 'FFSS': 2, 'CSCS': 1, 'CCSS': 1,
            'CSRS': 1,'RSRS': 1, 'RRSS': 1
        }
        
        self.tiles_sides = {
            'FFFF/m': [['F', 'F', 'F'],
                       ['F', 'm', 'F'],
                       ['F', 'F', 'F']], 
            
            'FFFR/m': [['F', 'F', 'F'],
                       ['R', 'm', 'F'],
                       ['F', 'F', 'F']], 
            
            'CFFF':   [['F', 'C', 'F'],
                       ['F', 'F', 'F'],
                       ['F', 'F', 'F']], 
            
            'FCFC/f': [['F', 'F', 'F'],
                       ['C', 'F', 'C'],
                       ['F', 'F', 'F']], 
            
            'CFCF/c': [['C', 'C', 'C'],
                       ['F', 'C', 'F'],
                       ['C', 'C', 'C']], 
            
            'CFCF/b': [['C', 'C', 'C'],
                       ['F', 'C', 'F'],
                       ['C', 'C', 'C']],
            
            'CCCC/b': [['C', 'C', 'C'],
                       ['C', 'C', 'C'],
                       ['C', 'C', 'C']], 
            
            'FFCC':   [['F', 'F', 'F'],
                       ['C', 'F', 'F'],
                       ['F', 'C', 'F']], 
            
            'CCFF':   [['F', 'C', 'C'],
                       ['F', 'F', 'C'],
                       ['F', 'F', 'F']],
            
            'CCFF/b': [['F', 'C', 'C'],
                       ['F', 'F', 'C'],
                       ['F', 'F', 'F']],
            
            'CCCF':   [['C', 'C', 'C'],
                       ['F', 'C', 'C'],
                       ['C', 'C', 'C']], 
            
            'CCCF/b': [['C', 'C', 'C'],
                       ['F', 'C', 'C'],
                       ['C', 'C', 'C']], 
            
            'CCCR':   [['C', 'C', 'C'],
                       ['R', 'C', 'C'],
                       ['C', 'C', 'C']], 
            
            'CCCR/b': [['C', 'C', 'C'],
                       ['R', 'C', 'C'],
                       ['C', 'C', 'C']],
             
            'FRFR':   [['F', 'F', 'F'],
                       ['R', 'R', 'R'],
                       ['F', 'F', 'F']],
            
            'FFRR':   [['F', 'F', 'F'],
                       ['R', 'F', 'F'],
                       ['F', 'R', 'F']], 
            
            'CRFR':   [['F', 'C', 'F'],
                       ['R', 'R', 'R'],
                       ['F', 'F', 'F']], 
            
            'CFRR':   [['F', 'C', 'F'],
                       ['R', 'F', 'F'],
                       ['F', 'R', 'F']], 
            
            'CRRF':   [['F', 'C', 'F'],
                       ['F', 'F', 'R'],
                       ['F', 'R', 'F']], 
            
            'CCRR':   [['F', 'C', 'C'],
                       ['R', 'F', 'C'],
                       ['F', 'R', 'F']], 
            
            'CCRR/b': [['F', 'C', 'C'],
                       ['R', 'F', 'C'],
                       ['F', 'R', 'F']], 
            
            'FRRR':   [['F', 'F', 'F'],
                       ['R', 'R', 'R'],
                       ['F', 'R', 'F']], 
            
            'CRRR':   [['F', 'C', 'F'],
                       ['R', 'R', 'R'],
                       ['F', 'R', 'F']],
            
            'RRRR':   [['F', 'R', 'F'],
                       ['R', 'R', 'R'],
                       ['F', 'R', 'F']], 
            
            'FSRS/m': [['F', 'F', 'F'],
                       ['S', 'm', 'S'],
                       ['F', 'R', 'F']], 
            
            'FFSF':   [['F', 'F', 'F'],
                       ['F', 'S', 'F'],
                       ['F', 'S', 'F']], 
            
            'FSFS':   [['F', 'F', 'F'],
                       ['S', 'S', 'S'],
                       ['F', 'F', 'F']], 
            
            'FFSS':   [['F', 'F', 'F'],
                       ['S', 'F', 'F'],
                       ['F', 'S', 'F']], 
            
            'CSCS':   [['F', 'C', 'F'],
                       ['S', 'S', 'S'],
                       ['F', 'C', 'F']], 
            
            'CCSS':   [['F', 'C', 'C'],
                       ['S', 'F', 'C'],
                       ['F', 'S', 'F']],
            
            'CSRS':   [['F', 'C', 'F'],
                       ['S', 'R', 'S'],
                       ['F', 'R', 'F']],
            
            'RSRS':   [['F', 'R', 'F'],
                       ['S', 'R', 'S'],
                       ['F', 'R', 'F']], 
            
            'RRSS':   [['F', 'R', 'F'],
                       ['S', 'F', 'R'],
                       ['F', 'S', 'F']]
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
