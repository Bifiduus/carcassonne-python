from carcassonne.Presentation.Interfaces.IGameService import IGameService
from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData
from carcassonne.Datas.TilesInfo import TilesInfo
from carcassonne.Datas.History import History, MoveRecord
from carcassonne.Datas.Serializer import parse_move, build_str


class RulesManager():
    
    def __init__(self, game):
        self.tiles_dict = {
            'FFFF': ['m'], 'FFFR': ['m'], 'CFFF': ['void'], 'FCFC': ['f'], 'CFCF': ['c', 'b'],
            'CCCC': ['b'], 'FFCC': ['void'], 'CCFF': ['void', 'b'], 'CCCF': ['void', 'b'], 'CCCR': ['void', 'b'], 'FRFR': ['void'],
            'FFRR': ['void'], 'CRFR': ['void'], 'CFRR': ['void'], 'CRRF': ['void'], 'CCRR': ['void', 'b'], 'FRRR': ['void'], 'CRRR': ['void'],
            'RRRR': ['void'], 'FSRS': ['m'], 'FFSF': ['void'], 'FSFS': ['void'], 'FFSS': ['void'], 'CSCS': ['void'], 'CCSS': ['void'],
            'CSRS': ['void'],'RSRS': ['void'], 'RRSS': ['void']
        }

        self.direction_list = ['N', 'E', 'S', 'W']
        self.direction_dict = {'N': 0, 'E': 1, 'S': 2, 'W': 3}
        
        self.data : IGraphData = game.get_game_configuration()
        
        self.TilesInfo = TilesInfo()
        self.history = History()

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
        tile2 =  self.data.get_verticies()[(int(tile2_details[0]))]
        rotation_tile2 = tile2.get_orientation()

        # direction index between 0 and 3 (0 being North, 3 being West) on tile1 that will face the orientation before rotation (which side of the tile we want to place is concerned)
        dir_idx = self.direction_dict[orientation_tile1]

        # compute the index on tile1 that will face the orientation after rotation
        # using modulo to wrap negatives (e.g. (2 - 3) % 4 == 3)
        index_tile1 = (dir_idx - rotation_tile1) % 4
        side1 = tile1[index_tile1]

        # same with tile2
        side2 = tile2.get_name()[self.direction_dict[orientation_tile2] - rotation_tile2 % 4]
        
        return side1 == side2
    
    def isLegalMove(self, move_parts):
        
        """
        Checks if the given move is legal in the current game state.
        
        Returns True if the move is legal, False otherwise.
        """
        counter = 0
        
        counter += 1
        if len(move_parts[counter]) == 1:
            if not self.TilesInfo.is_tile_left(move_parts[counter - 1] + '/' + move_parts[counter]):
                print("no tiles left of that type with that center")
                return False
            counter += 1   
        else :
            if not self.TilesInfo.is_tile_left(move_parts[counter - 1]):
                print("no tiles left of that type without center")
                return False 
            
        if not self.data.get_verticies()[int(move_parts[counter][0])].is_neighbor_free(self.direction_dict[move_parts[counter][1]]):
            print("the tile you try to attach yours to already has a neighbor on that side")
            return False
        
        if not self.areEqualSides(move_parts[0], move_parts[counter]):
            print("the tile you try to place doesn't match the tile you try to attach yours to")
            return False
        
        # Verify meeple placement if applicable 
        #TODO : can_place_meeple_on_tile_side(move_parts[0] : str, move_parts[counter] str, game : IGameService) -> bool
        '''counter += 1
        if len(move_parts) == counter - 1:
            if not self.data.canPlaceMeepleOnTileSide(move_parts[0], move_parts[counter], game):
                print("you can't place a meeple on that side of the tile you try to place")
                return False'''
        
        return True
    
    def placeTile(self, move): #ça marche pas encore sachant qu'il faut d'autres trucs implémentés mais voilà l'idée
        
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
            
        if len(move_parts) <= counter:
            print("the move misses the tile placement details")
            return
            
        #REGARDER COMMENT PRENDRE LE NOMBRE ENTIER ET PAS JUSTE LE PREMIER CHIFFRE (marche avec 7, mais pas avec 12 par exemple)
        if int(move_parts[counter][0]) >= self.data.get_turn_number():
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
            
        if not self.isLegalMove(move_parts):
            print("the move isn't valid")
            return
        
        #jouer le move dans les structures
        tile_pos = self.data.get_position(vertex_id=(int)(move_parts[counter - 1][0]), side=self.direction_dict[move_parts[counter - 1][1]])
        if(tile_pos is None):
            print("Error in getting position")
            return
        self.data.add_vertex(vertex_id=self.data.get_turn_number(), name=move_parts[0], orientation=int(move_parts[counter - 1][2]), position=tile_pos)  # example of adding the tile as a vertex in the graph, you would need to set neighbors and orientations based on the move details
        
        #enlever la tuile des tuiles disponibles
        tile_name = move_parts[0] + '/' + move_parts[1] if len(move_parts[1]) == 1 else move_parts[0]
        self.TilesInfo.remove_tile(tile_name)

        try:
            parsed = parse_move(move)
            record = MoveRecord(
                move_str="",
                player_id=1,
                tile_sides=parsed["tile_sides"],
                target_id=parsed["target_id"],
                target_side=parsed["target_side"],
                rotation=parsed["rotation"],
                meeple=parsed["meeple"],
                center=parsed.get("center"),
            )
            record.move_str = build_str(record)
            self.history.push_past(record)
            self.history.clear_future()
        except ValueError:
            pass
        
        print(move + " placed successfully.")
    

    def getGameHistory(self):
        return self.history.list_history()
    
    def placeMeeple(self, move):
        pass
        
    def playAI(self):
        pass

    def current_player_is_human(self) -> bool:
        #TODO : is_human_player(game : IGameService) -> bool
        return True
    
