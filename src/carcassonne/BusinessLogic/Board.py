"""This module defines the Board class, which is responsible for managing the game board in Carcassonne. 
It provides methods to add and remove tiles from the board, as well as to update the game state accordingly. 
The Board class interacts with the graph data structure that represents the game state, the tiles information, and the history of moves made during the game.
"""
from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData
from carcassonne.Datas.GraphData import GraphData
from carcassonne.Datas.History import History, MoveRecord
from carcassonne.BusinessLogic.Interfaces.ITilesInfo import ITilesInfo
from carcassonne.Datas.Serializer import build_str

class Board:
    
    def add_tile_to_board(self, move, graph: IGraphData, tiles_info: ITilesInfo, history: History, players) -> None:
        move_parts = move.split('/')
        #jouer le move dans les structures
        counter = 3 if len(move_parts[1]) == 1 else 2
        tile_pos = graph.get_position(vertex_id=(int)(move_parts[counter - 1][0]), side=tiles_info.direction_dict[move_parts[counter - 1][1]])
        if(tile_pos is None):
            print("Error in getting position")
            return
        turn = graph.get_turn_number()
        graph.add_vertex(vertex_id=turn, name=move_parts[0], middle=move_parts[1] if counter==3 else "", orientation=int(move_parts[counter - 1][2]), position=tile_pos)  # example of adding the tile as a vertex in the graph, you would need to set neighbors and orientations based on the move details
        
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
        tile_pos = graph.get_position(vertex_id=(int)(move_parts[counter - 1][0]), side=tiles_info.direction_dict[move_parts[counter - 1][1]])
        if(tile_pos is None):
            print("Error in getting position")
            return
        graph.remove_vertex(vertex_id=graph.get_turn_number()-1)  # example of removing the tile as a vertex in the graph
        
        #rajouter la tuile des tuiles disponibles
        tile_name = move_parts[0] + '/' + move_parts[1] if len(move_parts[1]) == 1 else move_parts[0]
        tiles_info.add_tile(tile_name)
