from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData
from carcassonne.Datas.GraphData import GraphData
from carcassonne.Datas.History import History, MoveRecord
from carcassonne.BusinessLogic.Interfaces.ITilesInfo import ITilesInfo
from carcassonne.Datas.Serializer import parse_move, build_str

class Board:
    
    def add_tile_to_board(self, move, graph: IGraphData, tiles_info: ITilesInfo, history: History) -> None:
        move_parts = move.split('/')
        #jouer le move dans les structures
        counter = 3 if len(move_parts[1]) == 1 else 2
        tile_pos = graph.get_position(vertex_id=(int)(move_parts[counter - 1][0]), side=tiles_info.direction_dict[move_parts[counter - 1][1]])
        if(tile_pos is None):
            print("Error in getting position")
            return
        graph.add_vertex(vertex_id=graph.get_turn_number(), name=move_parts[0], orientation=int(move_parts[counter - 1][2]), position=tile_pos)  # example of adding the tile as a vertex in the graph, you would need to set neighbors and orientations based on the move details
        
        #enlever la tuile des tuiles disponibles
        tile_name = move_parts[0] + '/' + move_parts[1] if len(move_parts[1]) == 1 else move_parts[0]
        tiles_info.remove_tile(tile_name)

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
            history.push_past(record)
            history.clear_future()
        except ValueError:
            pass