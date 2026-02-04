from carcassonne.IGameService import IGameService


class RulesEngine(IGameService):
    
    def __init__(self, data):
        self.tiles_dict = {
            'FFFF': ['m'], 'FFFR': ['m'], 'CFFF': ['void'], 'FCFC': ['f'], 'CFCF': ['c', 'b'],
            'CCCC': ['b'], 'FFCC': ['void'], 'CCFF': ['void', 'b'], 'CCCF': ['void', 'b'], 'CCCR': ['void', 'b'], 'FRFR': ['void'],
            'FFRR': ['void'], 'CRFR': ['void'], 'CFRR': ['void'], 'CRRF': ['void'], 'CCRR': ['void', 'b'], 'FRRR': ['void'], 'CRRR': ['void'],
            'RRRR': ['void'], 'FSRS': ['m'], 'FFSF': ['void'], 'FSFS': ['void'], 'FFSS': ['void'], 'CSCS': ['void'], 'CCSS': ['void'],
            'CSRS': ['void'],'RSRS': ['void'], 'RRSS': ['void']
        }

        self.direction_list = ['N', 'E', 'S', 'W']
        self.direction_dict = {'N': 0, 'E': 1, 'S': 2, 'W': 3}
        
        self.data = data

    def areEqualSides(self, tile1, tile2_details):
        """
        Checks if the sides of two tiles from the computed move are equal.

        This handles two formats for `tile2_details`:
        - a tile code (e.g. 'CRRF') in which case we compare the corresponding side
        - a move spec (e.g. '12N2') where the first number is the tile id, the second char is the orientation (N/S/W/E) 
            and second number is the rotation applied to the tile to place

        Rotation arithmetic uses Python's modulo so negative results wrap (e.g. (2 - 3) % 4 -> 3).

        Returns True if the sides are equal, False otherwise.
        """
        
        orientation_tile2 = tile2_details[1]
        orientation_tile1 = self.direction_list[(self.direction_dict[orientation_tile2] + 2) % 4]
            
        rotation_tile1 = int(tile2_details[2])
        rotation_tile2 = game.getTileRotation(int(tile2_details[0]))

        # direction index between 0 and 3 (0 being North, 3 being West) on tile1 that will face the orientation before rotation (which side of the tile we want to place is concerned)
        dir_idx = self.direction_dict[orientation_tile1]

        # compute the index on tile1 that will face the orientation after rotation
        # using modulo to wrap negatives (e.g. (2 - 3) % 4 == 3)
        index_tile1 = (dir_idx - rotation_tile1) % 4
        side1 = tile1[index_tile1]

        # same with tile2
        side2 = game.getTile(tile2_details[0])[self.direction_dict[orientation_tile2] - rotation_tile2 % 4]
        
        return side1 == side2
    
    def isLegalMove(self, move_parts, game):
        
        """
        Checks if the given move is legal in the current game state.
        
        Returns True if the move is legal, False otherwise.
        """
        counter = 0
        
        if not self.data.isTileLeft(move_parts[counter], game):
            return False
        
        counter += 1
        if len(move_parts[counter]) == 1:
            counter += 1
            
        if not game.isTileSideAttachable(move_parts[counter][0], move_parts[counter][1], game):
            return False
        
        if self.areEqualSides(move_parts[0], move_parts[counter]):
            return False
        
        # Verify meeple placement if applicable
        counter += 1
        if len(move_parts) == counter - 1:
            if not game.canPlaceMeepleOnTileSide(move_parts[0], move_parts[counter], game):
                return False
        
        return True
    
    def placeTile(self, move, game): #ça marche pas encore sachant qu'il faut d'autres trucs implémentés mais voilà l'idée
        
        """
        Tries to place a tile according to the computed move :
        - Checks if the move is a string.
        - Splits the move into parts.
        - Validates each part of the move.
        - Tests if the move is legal in the current game state.
        - If all checks pass, places the tile in the game structures.
        """
    
        counter = 0
        if not isinstance(move, str):
            print("the move needs to be a str\n")
            return
        
        move_parts = move.split('/')
        if not 2 <= len(move_parts) <= 4:
            print("the move is invalid, are you sure you computed it right?\n")
            return
        if move_parts[counter] not in self.tiles_dict:
            print("the tile you try to play doesn't exist, are you sure you computed it right?")
            return
        
        counter += 1
        if (len(move_parts[counter]) == 1):
            if move_parts[counter] not in self.tiles_dict[move_parts[counter - 1]]:
                print("the tile you try to place doesn't have that center")
                return  
            counter += 1
        else :
            if 'void' not in self.tiles_dict[move_parts[counter - 1]]:
                print("the tile you try to place needs a center")
                return
            
        if int(move_parts[counter][0]) >= game.getTurnNumber():
            print("the tile you try to attach yours to has an invalid number")
            return
        if move_parts[counter][1] not in self.direction_list:   
            print("the tile's side you try to attach yours on must be N, S, W or E")
            return      
        if not (0 <= int(move_parts[counter][2]) <= 3): 
            print("the rotation you apply to your tile must be between 0 and 3")
            return  
        
        counter += 1
        if (len(move_parts) == counter - 1):
            if move_parts[counter] not in (self.direction_list + ['C']):
                print("the tile's side you try to place a meeple on must be N, S, W, E or C")
                return
        if not self.isLegalMove(move_parts, game):
            print("the move isn't valid")
            return
        
        #jouer le move dans les structures
        print(move + " placed successfully.")
    
    def getGameStates(self):
        pass
    
    def placeMeeple(self, move):
        pass
        
    def playAI(self):
        pass
    