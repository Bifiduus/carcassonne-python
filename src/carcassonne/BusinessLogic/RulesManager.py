from carcassonne.Presentation.Interfaces.IGameService import IGameService
from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData
from carcassonne.BusinessLogic.Interfaces.ITilesInfo import ITilesInfo
from carcassonne.Datas.TilesInfo import TilesInfo
from carcassonne.Datas.History import History, MoveRecord


class RulesManager():
    
    def __init__(self, tiles_info: ITilesInfo):
        
        self.tiles_info = tiles_info

    def areEqualSides(self, tile1, tile2_details, graph: IGraphData):
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
        orientation_tile1 = self.tiles_info.direction_list[(self.tiles_info.direction_dict[orientation_tile2] + 2) % 4]
            
        rotation_tile1 = int(tile2_details[2])
        tile2 =  graph.get_verticies()[(int(tile2_details[0]))]
        rotation_tile2 = tile2.get_orientation()

        # direction index between 0 and 3 (0 being North, 3 being West) on tile1 that will face the orientation before rotation (which side of the tile we want to place is concerned)
        dir_idx = self.tiles_info.direction_dict[orientation_tile1]

        # compute the index on tile1 that will face the orientation after rotation
        # using modulo to wrap negatives (e.g. (2 - 3) % 4 == 3)
        index_tile1 = (dir_idx - rotation_tile1) % 4
        side1 = tile1[index_tile1]

        # same with tile2
        side2 = tile2.get_name()[self.tiles_info.direction_dict[orientation_tile2] - rotation_tile2 % 4]
        
        return side1 == side2
    
    def is_legal_move(self, move_parts, graph: IGraphData):
        
        """
        Checks if the given move is legal in the current game state.
        
        Returns True if the move is legal, False otherwise.
        """
        counter = 0
        
        counter += 1
        if len(move_parts[counter]) == 1:
            if not self.tiles_info.is_tile_left(move_parts[counter - 1] + '/' + move_parts[counter]):
                print("no tiles left of that type with that center")
                return False
            counter += 1   
        else :
            if not self.tiles_info.is_tile_left(move_parts[counter - 1]):
                print("no tiles left of that type without center")
                return False 
            
        if not graph.get_verticies()[int(move_parts[counter][0])].is_neighbor_free(self.tiles_info.direction_dict[move_parts[counter][1]]):
            print("the tile you try to attach yours to already has a neighbor on that side")
            return False
        
        if not self.areEqualSides(move_parts[0], move_parts[counter], graph):
            print("the tile you try to place doesn't match the tile you try to attach yours to")
            return False
        
        # Verify meeple placement if applicable 
        #TODO : can_place_meeple_on_tile_side(move_parts[0] : str, move_parts[counter] str, game : IGameService) -> bool
        '''counter += 1
        if len(move_parts) == counter - 1:
            if not graph.canPlaceMeepleOnTileSide(move_parts[0], move_parts[counter], game):
                print("you can't place a meeple on that side of the tile you try to place")
                return False'''
        
        return True
    
    def is_correctly_formed_move(self, move, graph: IGraphData):
        """
        Checks if the given move is correctly formed.

        This includes checks for:
        - Move being a string.
        - Move having the correct number of parts when split by '/'.
        - Valid tile code and center if applicable.
        - Valid target tile ID, orientation, and rotation.
        - Valid meeple placement if applicable.

        Returns True if the move is correctly formed, False otherwise.
        """
        
        counter = 0
        if not isinstance(move, str):
            print("the move needs to be a str\n")
            return
        
        move_parts = move.split('/')
        if not 2 <= len(move_parts) <= 4:
            print("the move is invalid, are you sure you computed it right?\n")
            return
        if move_parts[counter] not in self.tiles_info.tiles_dict:
            print("the tile you try to play doesn't exist, are you sure you computed it right?")
            return
        
        counter += 1
        if (len(move_parts[counter]) == 1):
            if move_parts[counter] not in self.tiles_info.tiles_dict[move_parts[counter - 1]]:
                print("the tile you try to place doesn't have that center")
                return  
            counter += 1
        else :
            if 'void' not in self.tiles_info.tiles_dict[move_parts[counter - 1]]:
                print("the tile you try to place needs a center")
                return
            
        if len(move_parts) <= counter:
            print("the move misses the tile placement details")
            return
            
        #REGARDER COMMENT PRENDRE LE NOMBRE ENTIER ET PAS JUSTE LE PREMIER CHIFFRE (marche avec 7, mais pas avec 12 par exemple)
        if int(move_parts[counter][0]) >= graph.get_turn_number():
            print("the tile you try to attach yours to has an invalid number")
            return
        if move_parts[counter][1] not in self.tiles_info.direction_list:   
            print("the tile's side you try to attach yours on must be N, S, W or E")
            return      
        if not (0 <= int(move_parts[counter][2]) <= 3): 
            print("the rotation you apply to your tile must be between 0 and 3")
            return  
        
        counter += 1
        if (len(move_parts) == counter - 1):
            if move_parts[counter] not in (self.tiles_info.direction_list + ['C']):
                print("the tile's side you try to place a meeple on must be N, S, W, E or C")
                return
            
        return True
        
    def check_move(self, move, graph: IGraphData):
        """
        Checks if the given move is valid in the current game state and prints the result.

        This method serves as a wrapper around  is_legal_move` to provide user feedback.
        """
        if not self.is_correctly_formed_move(move, graph=graph):
            return False
        
        if not self.is_legal_move(move.split('/'), graph):
            return False
        
        return True  

    def getGameHistory(self):
        return self.history.list_history()

    def current_player_is_human(self) -> bool:
        #TODO : is_human_player(game : IGameService) -> bool
        return True
    
