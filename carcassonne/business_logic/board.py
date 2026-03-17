"""Board management for Carcassonne.

This module adds/removes tiles and updates the graph, tile metadata, and move
history.
"""

import re
from carcassonne.business_logic.interfaces.i_graph_data import IGraphData
from carcassonne.business_logic.player import Player
from carcassonne.datas.history import History, MoveRecord
from carcassonne.business_logic.interfaces.i_tiles_info import ITilesInfo
from carcassonne.business_logic.graph_logic import GraphLogic
from carcassonne.business_logic.score_manager import ScoreManager
from carcassonne.datas.meeple_data import Meeple
from carcassonne.datas.tiles_info import Tile
from carcassonne.datas.serializer import parse_move, build_str

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
    def __init__(self):
        """Initialize Board with tracking for already-scored components."""
        self.scored_components = (
            set()
        )  # Track components that have already scored

    def add_tile_to_board(
        self,
        move: str,
        graph: IGraphData,
        tiles_info: ITilesInfo,
        history: History,
        players: dict[int, Player],
        players_order: list[int],
        current_player: Player,
    ) -> None:
        move_parts = move.split("/")
        # jouer le move dans les structures
        counter = 3 if len(move_parts[1]) == 1 else 2
        integers_placement = [
            int(x) for x in re.findall(r"\d+", move_parts[counter - 1])
        ]
        attach_direction = "".join(
            c for c in move_parts[counter - 1] if c.isalpha()
        )
        tile_pos = graph.get_position(
            vertex_id=integers_placement[0],
            side=tiles_info.direction_dict[attach_direction],
        )
        if tile_pos is None:
            print("Error in getting position")
            return
        turn = max(graph.get_verticies().keys(), default=-1) + 1
        current_player_id = current_player.get_id()
        tile_id = turn
        # example of adding the tile as a vertex in the graph, you would need
        # to set neighbors and orientations based on the move details
        graph.add_vertex(
            vertex_id=turn,
            name=move_parts[0],
            middle=move_parts[1] if counter == 3 else "",
            orientation=integers_placement[1],
            position=tile_pos,
        )

        graph_logic = GraphLogic()
        # example of updating lands components after adding a tile
        graph_logic.add_lands_components(
            tile_id=turn, graph=graph, tiles_info=tiles_info
        )

        # print(f"Updated lands components after adding tile {turn}")
        if counter == len(move_parts) - 1:
            # meeple
            land_pos = Tile.direction_matrix[integers_placement[1]][
                GraphLogic.match_matrix[move_parts[counter]][0]
            ][GraphLogic.match_matrix[move_parts[counter]][1]]
            set_name_to_place = None
            for land_type in graph.lands_components:
                for set_name, sets in graph.lands_components.get(
                    land_type
                ).items():
                    for tileid, directions in sets:
                        if tileid == tile_id and land_pos in directions:
                            set_name_to_place = set_name
            meeple = Meeple(
                player_id=current_player_id,
                tile_id=tile_id,
                position=tiles_info.meeple_placement_list.index(
                    move_parts[counter]
                ),
                lands_components=set_name_to_place,
            )
            graph.add_meeple(meeple)
            # print(turn)
            # print(len(players_order))
            # print(players_order[(turn - 1) % len(players_order)])
            # print(players[players_order[(turn - 1) % len(players_order)]])
            players[
                players_order[(turn - 1) % len(players_order)]
            ].remove_meeple()
        # print(f"Updated meeples after adding tile {turn}: {graph.meeples}")
        print(f"Updated meeples after adding tile {turn}: {graph.meeples}")

        # Score completed components at end of turn
        # Map player_id (0-based) to Player object
        ScoreManager.score_end_of_turn(
            graph, players, current_player_id, self.scored_components
        )

        # affiche les scores actuels dans la console
        print(f"-- Scores après le tour {turn} --")
        for player_id in sorted(players.keys()):
            player = players[player_id]
            print(f"Joueur {
                player_id +
                1} ({
                player.get_username()}): {
                player.get_score().score} pts")
        print("------------------------------")

        # enlever la tuile des tuiles disponibles
        tile_name = (
            move_parts[0] + "/" + move_parts[1]
            if len(move_parts[1]) == 1
            else move_parts[0]
        )
        tiles_info.remove_tile(tile_name)

        try:
            record = MoveRecord(
                move_str=move,
                player_id=current_player.get_id(),
                is_ai=current_player.is_ai,
            )
            history.push_past(record)
            history.clear_future()
        except ValueError:
            pass

    def remove_tile_from_board(
        self,
        move: str,
        graph: IGraphData,
        tiles_info: ITilesInfo,
        history: History,
        players: dict[int, Player],
    ) -> None:

        move_parts = move.split(":")[1].split("/")
        counter = 3 if len(move_parts[1]) == 1 else 2
        integers_placement = [
            int(x) for x in re.findall(r"\d+", move_parts[counter - 1])
        ]
        attach_direction = "".join(
            c for c in move_parts[counter - 1] if c.isalpha()
        )
        tile_pos = graph.get_position(
            vertex_id=integers_placement[0],
            side=tiles_info.direction_dict[attach_direction],
        )
        if tile_pos is None:
            print("Error in getting position")
            return

        tile_id = graph.get_turn_number() - 1
        # example of removing the tile as a vertex in the graph
        graph.remove_vertex(vertex_id=tile_id)
        graph.remove_meeple(tile_id, players)

        # rajouter la tuile des tuiles disponibles
        tile_name = (
            move_parts[0] + "/" + move_parts[1]
            if len(move_parts[1]) == 1
            else move_parts[0]
        )
        tiles_info.add_tile(tile_name)
