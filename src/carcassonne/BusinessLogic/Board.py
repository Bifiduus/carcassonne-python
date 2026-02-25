"""This module defines the Board class, which is responsible for managing the game board in Carcassonne. 
It provides methods to add and remove tiles from the board, as well as to update the game state accordingly. 
The Board class interacts with the graph data structure that represents the game state, the tiles information, and the history of moves made during the game.
"""
import re
from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData
from carcassonne.Datas.GraphData import GraphData
from carcassonne.Datas.History import History, MoveRecord
from carcassonne.BusinessLogic.Interfaces.ITilesInfo import ITilesInfo
from carcassonne.BusinessLogic.GraphLogic import GraphLogic
from carcassonne.Datas.MeepleData import Meeple
from carcassonne.Datas.TilesInfo import Tile
from carcassonne.Datas.Serializer import parse_move, build_str

NORTHWEST_MATRIX = (0, 0)
NORTH_MATRIX = (0, 1)
NORTHEAST_MATRIX = (0, 2)
WEST_MATRIX = (1, 0)
CENTER_MATRIX = (1, 1)
EAST_MATRIX = (1, 2)
SOUTHWEST_MATRIX = (2, 0)
SOUTH_MATRIX = (2, 1)
SOUTHEAST_MATRIX = (2, 2)

class Board:
    
    def add_tile_to_board(self, move, graph: IGraphData, tiles_info: ITilesInfo, history: History, players) -> None:
        move_parts = move.split('/')
        #jouer le move dans les structures
        counter = 3 if len(move_parts[1]) == 1 else 2
        integers_placement = [int(x) for x in re.findall(r'\d+', move_parts[counter - 1])]  
        attach_direction = ''.join(c for c in move_parts[counter - 1] if c.isalpha())
        tile_pos = graph.get_position(vertex_id=integers_placement[0], side=tiles_info.direction_dict[attach_direction])
        if(tile_pos is None):
            print("Error in getting position")
            return
        turn = graph.get_turn_number()
        tile_id = turn
        graph.add_vertex(vertex_id=turn, name=move_parts[0], middle=move_parts[1] if counter==3 else "", orientation=integers_placement[1], position=tile_pos)  # example of adding the tile as a vertex in the graph, you would need to set neighbors and orientations based on the move details
        
        graph_logic = GraphLogic()
        graph_logic.add_lands_components(tile_id=turn, graph=graph, tiles_info=tiles_info)  # example of updating lands components after adding a tile
        
        print(f"Updated lands components after adding tile {turn}: {graph.lands_components}")
        if counter == len(move_parts) - 1:
            #meeple
            land_pos = Tile.direction_matrix[integers_placement[1]][GraphLogic.match_matrix[move_parts[counter]][0]][GraphLogic.match_matrix[move_parts[counter]][1]]
            set_name_to_place = None
            for land_type in graph.lands_components:
                for set_name, sets in graph.lands_components.get(land_type).items():
                    for tileid, directions in sets:
                        if tileid == tile_id and land_pos in directions:
                            set_name_to_place = set_name
            meeple = Meeple(player_id=1, tile_id=tile_id, position=tiles_info.meeple_placement_list.index(move_parts[counter]), lands_components=set_name_to_place)
            graph.add_meeple(meeple)
        print(f"Updated meeples after adding tile {turn}: {graph.meeples}")
        #enlever la tuile des tuiles disponibles
        tile_name = move_parts[0] + '/' + move_parts[1] if len(move_parts[1]) == 1 else move_parts[0]
        tiles_info.remove_tile(tile_name)

        potential_meeple = move.split('/')[-1]
        if potential_meeple in tiles_info.tiles_parts_list:
            orientation=int(move_parts[counter - 1][2])
            direction_matrix_to_rotate = tiles_info.direction_matrix
            for i in range(orientation):
                direction_matrix_to_rotate = tiles_info.rotate_matrix_90(direction_matrix_to_rotate)
            matrix_coordinates = tiles_info.matrix_coordinates[potential_meeple]
            rotated_matrix_coordinates = direction_matrix_to_rotate[matrix_coordinates[0]][matrix_coordinates[1]]
            terrain_type = 'void'
            for dict in tiles_info.tiles_connections[tile_name]:
                for set in dict.values():
                    if potential_meeple in set:
                        terrain_type = dict.keys()
            if terrain_type == 'void':
                print("Error in getting terrain type for meeple placement")
                return
            #TODO
            #graph.add_meeple(turn, terrain_type=terrain_type, potential_meeple=potential_meeple) 
            players[turn % len(players)].remove_meeple()
    
        try:
            record = MoveRecord(
                move_str=move,
                player_id=1
            )
            history.push_past(record)
            history.clear_future()
        except ValueError:
            pass

    def remove_tile_from_board(self, move: str, graph: IGraphData, tiles_info: ITilesInfo, history: History) -> None:

        move_parts = move.split(':')[1].split('/')
        counter = 3 if len(move_parts[1]) == 1 else 2
        integers_placement = [int(x) for x in re.findall(r'\d+', move_parts[counter - 1])]  
        attach_direction = ''.join(c for c in move_parts[counter - 1] if c.isalpha())
        tile_pos = graph.get_position(vertex_id=integers_placement[0], side=tiles_info.direction_dict[attach_direction])
        if(tile_pos is None):
            print("Error in getting position")
            return
        
        tile_id = graph.get_turn_number()-1
        graph.remove_vertex(vertex_id=tile_id)  # example of removing the tile as a vertex in the graph
        graph.remove_meeple(tile_id)
        
        #rajouter la tuile des tuiles disponibles
        tile_name = move_parts[0] + '/' + move_parts[1] if len(move_parts[1]) == 1 else move_parts[0]
        tiles_info.add_tile(tile_name)
