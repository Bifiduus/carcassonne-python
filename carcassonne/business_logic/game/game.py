"""Game state and turn flow for Carcassonne.

This module implements `IGameService`, handling history, undo/redo,
rule checks, and persistence interactions.
"""

import random as r
import time
from typing import Any, List

from carcassonne.business_logic.game.commands_game import CommandsGame
from carcassonne.business_logic.game.end_game import EndGame
from carcassonne.business_logic.game.game_data import GameData
from carcassonne.business_logic.game.new_game import NewGame
from carcassonne.business_logic.game.undo_redo_manager import UndoRedoManager
from carcassonne.business_logic.interfaces.i_graph_data import IGraphData
from carcassonne.business_logic.player import Player
from carcassonne.presentation.interfaces.i_game_service import IGameService

OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}


class Game(IGameService):

    def __init__(
        self, graphData: IGraphData, nb_players: int, config_overrides=None
    ) -> None:
        self.game_data = GameData(graphData, nb_players, config_overrides)
        self.commands = CommandsGame(self.game_data, self)
        self.end_game_manager = EndGame(self.game_data)
        self.undo_redo_manager = UndoRedoManager(self.game_data)
        self.blitz_manager = self.game_data.blitz_manager
        self.new_game = NewGame(self.game_data, self)
        self.river = None

    def get_history(self) -> List[str]:
        """Return the current play history."""
        return self.game_data.history.list_history()

    def clear_undo_history(self) -> None:
        self.game_data.history.clear_future()

    def is_undo_history_empty(self) -> bool:
        return len(self.game_data.history.future_moves) == 0

    def get_game_configuration(self):
        return self.game_data.get_game_configuration()

    def save_config(self) -> None:
        self.game_data.game_configuration.save_config()

    def set_game_configuration(self, key: str, value) -> None:
        if key == "timeout":
            key = "time"
        self.game_data.game_configuration.settings[key] = value
        if key in ("blitz", "time"):
            self.game_data._initialize_blitz_state()

    def get_maximum_number_of_players(self) -> int:
        return self.game_data.get_maximum_number_of_players()

    def get_minimum_number_of_players(self) -> int:
        return self.game_data.get_minimum_number_of_players()

    def get_number_of_players(self) -> int:
        return self.game_data.get_number_of_players()

    def set_number_of_ai_players(self, num_players: int) -> None:
        self.game_data.add_players(num_players)
        self.game_data.number_of_ai_players = num_players

    def get_number_of_ai_players(self) -> int:
        return self.game_data.number_of_ai_players

    def get_current_player(self) -> Player:
        return self.game_data.get_current_player()

    def save_game_to_file(self, filename: str) -> int:
        return self.game_data.save_handler.save_game_to_file(filename)

    def load_game_from_file(self, filename: str) -> int:
        return self.game_data.save_handler.load_game_from_file(filename)

    def rotate_dirs(self, dirs: list, rotation: int) -> list:
        rotation = rotation % 4
        return dirs[-rotation:] + dirs[:-rotation]

    def generate_tile_ascii(self, vertex: Any) -> list[str]:
        dirs = list(vertex.get_name())  # [N, E, S, W]
        rotation = self.game_data.graph.get_vertex_orientation(
            vertex.get_id())  # 0 à 3
        meeples = self.game_data.graph.get_meeples()
        for meeple in meeples:
            if meeple.tile_id == vertex.get_id():
                pos_label = meeple.get_position_label()
                if pos_label in ["N", "E", "S", "W"]:
                    idx = ["N", "E", "S", "W"].index(pos_label)
                    dirs[idx] += f"{meeple.player_id}"
                elif pos_label in ["NW", "NE", "SE", "SW"]:
                    idx = ["NW", "NE", "SE", "SW"].index(pos_label)
                    dirs[idx - 1] += f"/{meeple.player_id}"
                else:
                    vertex.middle += f"{meeple.player_id}"

        n, e, s, w = self.rotate_dirs(dirs, rotation)
        m = "{:^3}".format(vertex.get_id())
        if vertex.get_middle() != "":
            m = "{:^5}".format(
                "[" + str(vertex.get_id()) + "/" + vertex.get_middle() + "]"
            )
        else:
            m = "{:^5}".format("[" + str(vertex.get_id()) + "]")
        space = 3 * " "

        return [
            space + "{:^5}".format(n) + space,
            "{:^3}".format(w) + "{:^5}".format(m) + "{:^3}".format(e),
            space + "{:^5}".format(s) + space,
        ]

    def get_board(self) -> list[Any] | None:
        vertices = list(self.game_data.graph.get_verticies().values())

        if not vertices:
            print("No vertices.")
            return

        positions = [v.get_position() for v in vertices]

        min_x = min(x for x, y in positions)
        min_y = min(y for x, y in positions)
        max_x = max(x for x, y in positions)
        max_y = max(y for x, y in positions)

        width = max_x - min_x + 1
        height = max_y - min_y + 1

        board = [[None for _ in range(width)] for _ in range(height)]

        for v in vertices:
            x, y = v.get_position()
            nx = x - min_x
            ny = y - min_y
            board[ny][nx] = self.generate_tile_ascii(v)

        self.print_board(board)
        return vertices

    def get_board_data(self) -> list[dict]:
        """
        Retourne une liste exploitable directement par la GUI.
        """
        vertices = self.game_data.graph.get_vertices_data()

        return list(vertices.values())

    def get_tile_data(self, tile: str) -> None:
        """
        Retourne une liste exploitable directement par la GUI.
        """
        vertice = self.game_data.graph.get_vertice_data(tile)

        return None

    def get_meeples_data(self) -> list[dict]:
        """
        Retourne une liste exploitable directement par la GUI.
        """
        meeples = self.game_data.graph.get_meeples()

        return [vars(meeple) for meeple in meeples]

    def print_board(self, board: list[list]) -> None:
        TILE_HEIGHT = 3
        EMPTY_TILE = [" " * 9] * TILE_HEIGHT

        for row in board:  # chaque ligne de tuiles
            for i in range(TILE_HEIGHT):  # chaque ligne ASCII interne
                line = []
                for tile in row:
                    if tile is None:
                        line.append(EMPTY_TILE[i])
                    else:
                        line.append(tile[i])
                print("   ".join(line))
            print()  # espace entre lignes de tuiles

    def get_close_neighbors(
        self, x: int, y: int
    ) -> tuple[int | None, int | None]:
        return self.game_data.graph.find_neighbor_at(x, y)

    def add_online_players(self, players: list[Player]) -> str:
        return self.new_game.start_online_game(players)

    def draw_tile(self) -> str | None:
        return self.game_data.deck_manager.draw_tile()

    def shuffle_deck(self, algo=None, seed=None) -> int:
        return self.game_data.deck_manager.shuffle_deck(algo, seed)

    def play_move(self, move: str) -> bool:
        return self.game_data.play_move(move)

    def play_ai_turn(self) -> None:
        self.game_data.play_ai_turn(self)

    def start_new_game(self, players_order: list[int] | None = None,
                       seed: int | None = None) -> None:
        return self.new_game.start_new_game(players_order, seed)

    def end_game(self) -> bool:
        return self.end_game_manager.end_game()

    def undo(self) -> None:
        self.undo_redo_manager.undo()

    def redo(self) -> None:
        self.undo_redo_manager.redo()

    def provide_hint(self) -> str:
        return self.commands.provide_hint()

    def get_all_players_remaining_time_seconds(self) -> List[tuple[int, float]]:
        return self.game_data.blitz_manager.get_all_players_remaining_time_seconds()

    def get_current_player_remaining_time_seconds(self) -> float | None:
        return self.game_data.blitz_manager.get_player_remaining_time_seconds(self.game_data.get_current_player().get_id())

    def get_player_remaining_time_seconds(self, player_id: int) -> float | None:
        return self.game_data.blitz_manager.get_player_remaining_time_seconds(player_id)

    def tick_blitz(self) -> bool:
        return self.game_data.blitz_manager.tick_blitz()

    def get_timeout_message(self) -> str:
        return self.game_data.blitz_manager.get_timeout_message()
