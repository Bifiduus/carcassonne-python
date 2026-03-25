"""Game state and turn flow for Carcassonne.

This module implements `IGameService`, handling history, undo/redo,
rule checks, and persistence interactions.
"""

import random as r
import time
from typing import Any, List

from carcassonne.business_logic.game.blitz_manager import BlitzManager
from carcassonne.business_logic.game.commands_game import CommandsGame
from carcassonne.business_logic.game.deck_manager import DeckManager
from carcassonne.business_logic.game.end_game import EndGame
from carcassonne.business_logic.game.game_data import GameData
from carcassonne.business_logic.game.new_game import NewGame
from carcassonne.business_logic.game.river_manager import RiverManager
from carcassonne.business_logic.game.undo_redo_manager import UndoRedoManager
from carcassonne.business_logic.interfaces.i_graph_data import IGraphData
from carcassonne.business_logic.player import Player
from carcassonne.business_logic.save_handler import SaveHandler
from carcassonne.business_logic.score_manager import ScoreManager
from carcassonne.datas.serializer import parse_move
from carcassonne.presentation.interfaces.i_game_service import IGameService

OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}


class Game(IGameService):

    def __init__(
        self, graphData: IGraphData, nb_players: int, config_overrides=None
    ) -> None:
        self.game_data = GameData(graphData, nb_players, config_overrides)
        self.save_handler = SaveHandler(self)
        self.score_manager = ScoreManager()
        self.blitz_manager = BlitzManager(self.game_data)
        self.undo_redo_manager = UndoRedoManager(self.blitz_manager, self.game_data)
        self.end_game_manager = EndGame(self.game_data, self.blitz_manager, self.score_manager)
        self.river_manager = RiverManager(self.game_data)
        self.deck_manager = DeckManager(self.game_data, self.blitz_manager, self.river_manager)
        self.commands = CommandsGame(self.blitz_manager, self.deck_manager, self.game_data, self)
        self.new_game = NewGame(self.river_manager, self.deck_manager, self.blitz_manager, self.game_data, self)
        self.river = None
        self.start_new_game()

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
            self.blitz_manager._initialize_blitz_state()

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
    
    def get_players_order(self) -> list[int]:
        return self.game_data.players_order

    def get_current_player(self) -> Player:
        return self.game_data.get_current_player()

    def save_game_to_file(self, filename: str) -> int:
        return self.save_handler.save_game_to_file(filename)

    def load_game_from_file(self, filename: str) -> int:
        return self.save_handler.load_game_from_file(filename)

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
        return self.deck_manager.draw_tile()

    def shuffle_deck(self, algo=None, seed=None) -> int:
        return self.deck_manager.shuffle_deck(algo, seed)

    def play_move(self, move: str) -> bool:
        """
        Tries to place a tile according to the computed move :
        - Checks if the move is a string.
        - Splits the move into parts.
        - Validates each part of the move.
        - Tests if the move is legal in the current game state.
        - If all checks pass, places the tile in the game structures.
        """

        timed_out_now = self.tick_blitz()
        if timed_out_now:
            return False
        if not self.blitz_manager._ensure_current_player_playable():
            return False

        if (
            self.game_data.players_order[self.game_data.current_player_order_list]
            != self.get_current_player().get_id()
        ):
            print("It is not your turn to play.")
            expected_player = self.game_data.players_order[
                self.current_player_order_list
            ]
            print(
                "The one: "
                f"{expected_player} {self.current_player_order_list}. "
                f"You: {self.get_current_player()}"
            )
            turn = max(self.game_data.graph.get_verticies().keys(),
                       default=-1) + 1
            print(f"turn:{turn}")
            print(self.game_data.players_order)
            return False
        if self.game_data.current_hand is None:
            print("Vous devez piocher une tuile avant de jouer.")
            return False

        tile_code = self.game_data.extract_tile_code(move)
        if tile_code is not None and tile_code != self.game_data.current_hand:
            print(f"Vous devez jouer la tuile en main: {self.current_hand}")
            return False

        try:
            parsed_move = parse_move(move)
        except ValueError:
            return False
        current_player_meeples = self.get_current_player().get_meeples()
        if parsed_move.get("meeple") and current_player_meeples <= 0:
            print("No meeple remaining")
            return False

        ok = self.game_data.rules_manager.check_move(
            move,
            self.game_data.graph,
            current_player_id=self.get_current_player().get_id(),
        )
        if ok:
            current_player = self.get_current_player()
            self.game_data.board.add_tile_to_board(
                move,
                self.game_data.graph,
                self.game_data.tiles_info,
                self.game_data.history,
                self.game_data.players,
                self.game_data.players_order,
                current_player,
            )
            print(move + " placed successfully.")
            self.game_data.current_hand = None
            self.game_data.current_player_order_list = (
                self.game_data.current_player_order_list + 1
            ) % self.get_number_of_players()
            self.blitz_manager._ensure_current_player_playable()
            """vertices = self.graph.get_verticies()
            for vertex in vertices.values():
                print(vertex.get_neighbors())"""
            return True
        """vertices = self.graph.get_verticies()
        for vertex in vertices.values():
            print(vertex.get_neighbors())
        print('i failed the test')"""
        return False

    def play_ai_turn(self, game=None) -> None:
        from carcassonne.business_logic.ai_model import RandomPlayer
        from carcassonne.business_logic.ai_model import ExpectimaxPlayer
        from carcassonne.business_logic.ai_model import MCTSPlayer

        if game is None:
            raise ValueError("game parameter is required for play_ai_turn")

        self.tick_blitz()
        if not self.blitz_manager._ensure_current_player_playable():
            return
        if not self.get_current_player().is_ai_player():
            return

        ai_player = self.get_current_player()
        print(f"AI Player {ai_player.get_username()} is thinking...")
        self.deck_manager.draw_tile()
        if self.game_data.current_hand is None:
            return
        ai_time = self.get_game_configuration().get("ai_time")
        model = None
        move = None
        eval_score = None
        if self.get_game_configuration().get("ai_mode") == "random":
            model = RandomPlayer()
            move = model.random_move(self.game_data.current_hand, game)
        elif self.get_game_configuration().get("ai_mode") == "minimax":
            start_time = time.time()
            depth = self.get_game_configuration().get("ai_minimax_depth", 5)
            model = ExpectimaxPlayer(
                game, start_time, ai_time or 10.0, depth or 5)
            eval_score, move = model.search(
                game,
                depth=model.depth_max,
                alpha=float("-inf"),
                beta=float("inf"),
                player_to_max=ai_player.get_id(),
                next_player=ai_player.get_id(),
            )
        elif self.get_game_configuration().get("ai_mode") == "mcts":
            start_time = time.time()
            eval_fn_name = self.get_game_configuration().get(
                "ai_mcts_selection", "uct"
            )
            model = MCTSPlayer(
                game, start_time, ai_time or 10.0, eval_fn_name or "uct")
            move = model.mcts(game)
        if not move:
            print(
                f"AI Player {ai_player.get_username()} has no legal move."
            )
            return
        if eval_score is None:
            print(
                f"AI Player {ai_player.get_username()} chooses move: {move}"
            )
        else:
            print(
                f"AI Player {ai_player.get_username()} chooses move: {move} "
                f"with evaluation score: {eval_score}"
            )
        # print("main avant de jouer le coup" + self.current_hand)
        move_played = self.play_move(move)
        if not move_played:
            fallback_played = False
            try:
                parsed = parse_move(move)
            except ValueError:
                parsed = {}

            # AI can still produce meeple moves from simulations where stock
            # differs from the live state. Retry once without meeple.
            if parsed.get("meeple") and ai_player.get_meeples() <= 0:
                fallback_move = move.rsplit("/", 1)[0]
                print(
                    "AI move rejected (no meeples left). "
                    f"Retrying without meeple: {fallback_move}"
                )
                fallback_played = self.play_move(fallback_move)

            if not fallback_played:
                print(
                    f"AI Player {ai_player.get_username()} produced an "
                    "invalid move."
                )
                return

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
        return self.blitz_manager.get_all_players_remaining_time_seconds()

    def get_current_player_remaining_time_seconds(self) -> float | None:
        return self.blitz_manager.get_player_remaining_time_seconds(self.game_data.get_current_player().get_id())

    def get_player_remaining_time_seconds(self, player_id: int) -> float | None:
        return self.blitz_manager.get_player_remaining_time_seconds(player_id)

    def tick_blitz(self) -> bool:
        return self.blitz_manager.tick_blitz()

    def get_timeout_message(self) -> str:
        return self.blitz_manager.get_timeout_message()
