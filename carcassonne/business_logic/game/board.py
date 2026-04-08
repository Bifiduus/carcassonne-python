"""Board management for Carcassonne.

This module adds/removes tiles and updates the graph, tile metadata, and move
history.
"""

import sys
import re
from carcassonne.business_logic.interfaces.i_graph_data import IGraphData
from carcassonne.business_logic.player import Player
from carcassonne.datas.history import History, MoveRecord
from carcassonne.business_logic.interfaces.i_tiles_info import ITilesInfo
from carcassonne.business_logic.graph_logic import GraphLogic
from carcassonne.business_logic.score_manager import ScoreManager
from carcassonne.datas.meeple_data import Meeple
from carcassonne.datas.tiles_info import Tile

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
    MEEPLE_ROTATION_MAP = {
        "N": "E",
        "E": "S",
        "S": "W",
        "W": "N",
        "NE": "SE",
        "SE": "SW",
        "SW": "NW",
        "NW": "NE",
        "C": "C",
    }

    def __init__(self):
        """Initialize Board with tracking for already-scored components."""
        self.scored_components = (
            set()
        )  # Track components that have already scored
        self._last_tile_added_log_info = None
        self._last_meeple_log_info = None
        self._last_scoring_log_events = []

    def consume_last_tile_added_log_info(self):
        """Return and clear the latest tile-added debug payload."""
        payload = self._last_tile_added_log_info
        self._last_tile_added_log_info = None
        return payload

    def consume_last_meeple_log_info(self):
        """Return and clear the latest meeple placement log payload."""
        payload = self._last_meeple_log_info
        self._last_meeple_log_info = None
        return payload

    def consume_last_scoring_log_events(self):
        """Return and clear scoring log payloads for the latest move."""
        payload = list(self._last_scoring_log_events)
        self._last_scoring_log_events = []
        return payload

    @staticmethod
    def _normalize_meeple_position(position: str, rotation: int) -> str:
        """Convert a rotated meeple position into the tile's base
        orientation."""
        rotation = rotation % 4
        steps = (-rotation) % 4
        for _ in range(steps):
            position = Board.MEEPLE_ROTATION_MAP[position]
        return position

    def add_tile_to_board(
        self,
        move: str,
        graph: IGraphData,
        tiles_info: ITilesInfo,
        history: History,
        players: dict[int, Player],
        players_order: list[int],
        current_player: Player,
        record_history: bool = True,
    ) -> None:
        self._last_tile_added_log_info = None
        self._last_meeple_log_info = None
        self._last_scoring_log_events = []
        move_parts = move.split("/")
        # jouer le move dans les structures
        counter = 3 if len(move_parts[1]) == 1 else 2
        integers_placement = [
            int(x) for x in re.findall(r"\d+", move_parts[counter - 1])
        ]
        attach_direction = "".join(
            c for c in move_parts[counter - 1] if c.isalpha()
        )
        tile_pos = graph.get_adjacent_position(
            vertex_id=integers_placement[0],
            side=tiles_info.direction_dict[attach_direction],
        )
        if tile_pos is None:
            print("Error in getting position", file=sys.stderr)
            return
        turn = max(graph.get_vertices().keys(), default=-1) + 1
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
        self._last_tile_added_log_info = (tile_id, move_parts[0], tile_pos)

        graph_logic = GraphLogic()
        # example of updating lands components after adding a tile
        graph_logic.add_lands_components(
            tile_id=turn, graph=graph, tiles_info=tiles_info
        )

        if counter == len(move_parts) - 1:
            if current_player.get_meeples() > 0:
                vertex = graph.get_vertex(tile_id)
                if vertex is not None:
                    side_placement = move_parts[counter]
                    side_x, side_y = GraphLogic.match_matrix[side_placement]
                    land_type = vertex.get_matrix()[side_x][side_y]

                    if land_type and land_type in graph.lands_components:
                        integer_placement_1 = integers_placement[1]
                        land_pos = Tile.direction_matrix[integer_placement_1][
                            side_x
                        ][side_y]
                        set_name_to_place = None
                        for set_name, sets in graph.lands_components[
                            land_type
                        ].items():
                            for tileid, directions in sets:
                                if (
                                    tileid == tile_id
                                    and land_pos in directions
                                ):
                                    set_name_to_place = set_name
                                    break
                            if set_name_to_place is not None:
                                break

                        if set_name_to_place is not None and not any(
                            meeple.lands_components == set_name_to_place
                            and meeple.player_id != current_player_id
                            for meeple in graph.get_meeples()
                        ):
                            meeple_position = move_parts[counter]
                            if integer_placement_1 != 0:
                                meeple_position = (
                                    self._normalize_meeple_position(
                                        meeple_position,
                                        integer_placement_1,
                                    )
                                )

                            meeple = Meeple(
                                player_id=current_player_id,
                                tile_id=tile_id,
                                position=(
                                    tiles_info.meeple_placement_list.index(
                                        meeple_position
                                    )
                                ),
                                lands_components=set_name_to_place,
                            )
                            graph.add_meeple(meeple)
                            players[current_player_id].remove_meeple()
                            self._last_meeple_log_info = (
                                current_player_id,
                                meeple_position,
                                set_name_to_place,
                            )

        # Score completed components at end of turn
        # Map player_id (0-based) to Player object
        ScoreManager.score_end_of_turn(
            graph,
            players,
            current_player_id,
            self.scored_components,
            emit_logs=False,
            log_events=self._last_scoring_log_events,
        )

        # display current scores in the console
        """print(f"-- Scores after turn {turn} --")
        for player_id in sorted(players.keys()):
            player = players[player_id]
            print(
                f"Player {player_id + 1} "
                f"({player.get_username()}): {player.get_score().score} pts"
            )
        print("------------------------------")
        """

        # remove the tile from available tiles
        tile_name = (
            move_parts[0] + "/" + move_parts[1]
            if len(move_parts[1]) == 1
            else move_parts[0]
        )
        tiles_info.remove_tile(tile_name)

        if record_history:
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
        tile_pos = graph.get_adjacent_position(
            vertex_id=integers_placement[0],
            side=tiles_info.direction_dict[attach_direction],
        )
        if tile_pos is None:
            print("Error in getting position", file=sys.stderr)
            return

        tile_id = max(graph.get_vertices().keys(), default=-1)
        # example of removing the tile as a vertex in the graph
        graph.remove_vertex(vertex_id=tile_id)
        graph.remove_meeple(tile_id, players)

        # add the tile back to available tiles
        tile_name = (
            move_parts[0] + "/" + move_parts[1]
            if len(move_parts[1]) == 1
            else move_parts[0]
        )
        tiles_info.add_tile(tile_name)
