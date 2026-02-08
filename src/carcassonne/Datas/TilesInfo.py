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

        self.tiles_parts_list = ['NW', 'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'C']
        self.direction_list = ['N', 'E', 'S', 'W']
        self.direction_dict = {'N': 0, 'E': 1, 'S': 2, 'W': 3}
        
        self.direction_matrix = [['NW', 'N', 'NE'], 
                                 ['W', 'C', 'E'], 
                                 ['SW', 'S', 'SE']]
        
        self.matrix_coordinates = {'NW' : (0,0), 'N' : (0,1), 'NE' : (0,2), 'E' : (1,2), 'SE' : (2,2), 'S' : (2,1), 'SW' : (2,0), 'W' : (1,0), 'C' : (1,1)}
        
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
            'FFFF/m': {'F' : [['N','E','S','W']]}, 'FFFR/m': {'F' : [['N','E','S']], 'R' : [['W']]}, 'CFFF': {'C' : [['N']], 'F' : [['E','S','W','C']]}, 
            'FCFC/f': {'F' : [['N','S','C']], 'C' : [['E'], ['W']]}, 'CFCF/c': {'C' : [['N','S','C']], 'F' : [['E'],['W']]}, 'CFCF/b': {'C' : [['N','S','C']], 'F' : [['E'],['W']]},
            'CCCC/b': {'C' : [['N','E','S','W','C']]}, 'FFCC': {'F' : [['N','E','C']], 'C' : [['S'],['W']]}, 'CCFF': {'C' : [['N','E']], 'F' : [['S','W','C']]}, 
            'CCFF/b': {'C' : [['N','E']], 'F' : [['S','W','C']]}, 'CCCF': {'C' : [['N','E','S','C']], 'F' : [['W']]}, 'CCCF/b': {'C' : [['N','E','S','C']], 'F' : [['W']]}, 
            'CCCR': {'C' : [['N','E','S','C']], 'R' : [['W']]}, 'CCCR/b': {'C' : [['N','E','S','C']], 'R' : [['W']]}, 'FRFR': {'F' : [['N','NE','NW'],['S','SE','SW']], 'R' : [['E','W','C']]},
            'FFRR': {'F' : [['N','E','SE','NW','C'], ['SW','NW']], 'R' : [['S','W']]}, 'CRFR': {'C' : [['N']], 'R' : [['E','W','C']], 'F' : [['SE','S','SW'],['NE','N','NW']]}, 
            'CFRR': {'C' : [['N']], 'F' : [['E','SE','NW','C'], ['SW','NW']], 'R' : [['S','W']]}, 'CRRF': {'C' : [['N']], 'R' : [['E','S']], 'F' : [['NE','SW','W'], ['SE','NW']]}, 
            'CCRR': {'C' : [['N','E']], 'R' : [['S','W']], 'F': [['SE','NW'], ['SW','NW']]}, 'CCRR/b': {'C' : [['N','E']], 'R' : [['S','W']], 'F': [['SE','NW'], ['SW','NW']]}, 
            'FRRR': {'F' : [['N','NE','NW'], ['SE','S'], ['SW','W']], 'R' : [['E','S','W','C']]}, 
            'CRRR': {'C' : [['N']], 'F': [['NE','NW'], ['SE','S'], ['SW','W']], 'R' : [['E','S','W','C']]},
            'RRRR': {'R' : [['N','E','S','W','C']], 'F' : [['NW','NW'], ['NE','NE'], ['SE','SE'], ['SW','SW']]}, 
            'FSRS/m': {'F' : [['N','NE','NW'], ['SE','S'], ['SW','W']], 'S' : [['E','W']], 'R': [['S']]}, 'FFSF': {'F' : [['N','E','S','W']], 'S' : [['S','C']]}, 
            'FSFS': {'F' : [['N','NE','NW'], ['S','SE','SW']], 'S' : [['E','W']]}, 'FFSS': {'F' : [['N','E','SE','NW'], ['SW','NW']], 'S' : [['S','W']]}, 
            'CSCS': {'C' : [['N'],['S']], 'S' : [['E','W']], 'F': [['NE','NW'], ['SE','SW']]}, 'CCSS': {'C' : [['N','E']], 'S' : [['S','W']], 'F': [['SE','NW'], ['SW','NW']]},
            'CSRS': {'C' : [['N']], 'S' : [['E','W']], 'R' : [['W','C']]},'RSRS': {'R' : [['N','S']], 'S' : [['E','W']]}, 
            'RRSS': {'R' : [['N','E']], 'S' : [['S','W']], 'F' : [['NW','SE','S','NW'], ['NE','NE'], ['SW','SW']]}
        }
    
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
        rotated = [['' for _ in range(n)] for _ in range(m)]
        
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
    
    def remove_tile(self, tile_code: str) -> None:
        """
        Decreases the count of the specified tile type by one.

        Raises a ValueError if there are no tiles left of that type.
        """
        if self.tiles_count.get(tile_code, 0) <= 0:
            raise ValueError(f"No tiles left of type: {tile_code}")
        self.tiles_count[tile_code] -= 1
