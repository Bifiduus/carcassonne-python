"""Game state and turn flow for Carcassonne.

This module implements `IGameService`, handling history, undo/redo,
rule checks, and persistence interactions.
"""

import random as r
import time
from typing import Any, List

from carcassonne.business_logic.score_manager import ScoreManager
from carcassonne.datas.deck import Deck
from carcassonne.datas.seed import Seed
from carcassonne.datas.serializer import parse_move
from carcassonne.business_logic.interfaces.i_graph_data import IGraphData
from carcassonne.business_logic.player import Player
from carcassonne.business_logic.rules_manager import RulesManager
from carcassonne.business_logic.board import Board
from carcassonne.datas.games_repository import GameRepository
from carcassonne.datas.game_configuration import GameConfiguration
from carcassonne.presentation.interfaces.i_game_service import IGameService
from carcassonne.datas.history import History
from carcassonne.business_logic.interfaces.i_tiles_info import ITilesInfo
from carcassonne.datas.tiles_info import TilesInfo
from carcassonne.business_logic.save_handler import SaveHandler
from carcassonne.business_logic.game_mode_manager import GameModeManager

OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}


class Game(IGameService):

    def __init__(
        self, graphData: IGraphData, nb_players: int, config_overrides=None
    ) -> None:
        self.game_configuration = GameConfiguration(config_overrides)
        self.game_repository: GameRepository = GameRepository()
        self.graph: IGraphData = graphData
        self.tiles_info: ITilesInfo = TilesInfo()
        self.rules_manager: RulesManager = RulesManager(self.tiles_info)
        self.history: History = History()
        self.board: Board = Board()
        self.deck = Deck()
        self.seed = None
        self.maximum_number_of_players = 5
        self.minimum_number_of_players = 2
        self.number_of_ai_players = 0
        self.default_seed = None
        self.shuffle_algo = "fisher-yates"
        self.current_hand = None
        self.save_file = None
        self.players: dict[int, Player] = {}
        self.players[0] = Player(0, "Player 0", "green")
        self.players_order: list[int] = [0]
        self.add_players(nb_players - 1)
        self.shuffle_players_order()
        self.current_player_order_list = 0
        self.save_handler = SaveHandler(self)
        self.score_manager = ScoreManager()
        self.error_message = ""
        self._end_game_scored = False
        self.game_mode_manager = GameModeManager(self)
        self._initialize_mode_state()

    def _configured_blitz_minutes(self) -> int:
        return self.game_mode_manager.get_configured_blitz_minutes()

    def _is_blitz_enabled(self) -> bool:
        return self.game_mode_manager.get_mode() == "blitz"

    def _initialize_mode_state(self) -> None:
        self.game_mode_manager.reset_for_current_state()

    def _initialize_blitz_state(self) -> None:
        self._initialize_mode_state()

    def _has_playable_player(self) -> bool:
        return self.game_mode_manager.has_playable_player()

    def _advance_to_next_playable_player(self) -> bool:
        return self.game_mode_manager.advance_to_next_playable_player()

    def skip_current_player(self) -> bool:
        return self.game_mode_manager.skip_current_player()

    def _ensure_current_player_playable(self) -> bool:
        return self.game_mode_manager.ensure_current_player_playable()

    # new method qui:
    # recréer players avec données de repo
    # (dans attributs de fonction), nb de players
    def start_online_game(self, players: list[Player]):
        if len(players) > self.get_maximum_number_of_players():
            max_players = self.get_maximum_number_of_players()
            return (
                "Error, too many players: "
                f"Maximum players is {max_players}"
            )
        self.history.clear_history()
        self.graph.reset_graph()
        self.current_hand = None
        self.board = Board()
        self.deck = Deck()
        self.tiles_info = TilesInfo()
        self.rules_manager = RulesManager(self.tiles_info)
        self.players.clear()
        self.add_online_players(players)
        self.shuffle_deck()
        self.shuffle_players_order()
        self.current_player_order_list = 0
        self._end_game_scored = False
        self._initialize_mode_state()
        return "Starting the game."

    def start_new_game(
        self,
        players_order: list[int] | None = None,
        seed: int | None = None,
    ) -> None:
        """Start a new game by clearing the play history, undo history,
        and resetting the graph and game repository.
        """
        self.history.clear_history()
        self.graph.reset_graph()
        self.board = Board()
        self.deck = Deck()
        self.current_hand = None
        self.tiles_info = TilesInfo()
        self.rules_manager = RulesManager(self.tiles_info)
        if players_order is not None:
            self.players_order = players_order
        else:
            self.shuffle_players_order()
        self.shuffle_deck(None, seed)
        self.current_player_order_list = 0
        self._end_game_scored = False
        self._initialize_mode_state()
        while self.get_current_player().is_ai_player():
            if self.end_game():
                break
            previous_player_id = self.get_current_player().get_id()
            self.play_ai_turn()
            if self.end_game():
                break
            if self.get_current_player().get_id() == previous_player_id:
                break

    def undo(self) -> None:
        """Undo the last human move and subsequent AI moves."""
        from .ai_model import is_ai_player

        if not self._ensure_current_player_playable():
            return

        if (
            self.rules_manager.current_player_is_human()
            and self.history.past_moves
        ):
            previous_play = self.history.pop_past()
            self.history.push_future(previous_play)
            while self.history.past_moves and is_ai_player(
                self.history.past_moves[-1]
            ):
                previous_play = self.history.pop_past()
                self.history.push_future(previous_play)

            self._rebuild_state_from_history()

    def redo(self) -> None:
        """Redo the last undone human move and subsequent AI moves."""
        from .ai_model import is_ai_player

        if not self._ensure_current_player_playable():
            return

        if (
            self.rules_manager.current_player_is_human()
            and self.history.future_moves
        ):
            last_unplayed_move = self.history.pop_future()
            self.history.push_past(last_unplayed_move)
            while self.history.future_moves and is_ai_player(
                self.history.future_moves[-1]
            ):
                self.history.push_past(self.history.pop_future())

            self._rebuild_state_from_history()

    def _rebuild_state_from_history(self) -> None:
        """Rebuild full game state from past moves to keep data coherent."""
        past_moves = list(self.history.past_moves)

        self.graph.reset_graph()
        self.board = Board()
        self.tiles_info = TilesInfo()
        self.rules_manager = RulesManager(self.tiles_info)
        self.current_hand = None

        for player in self.players.values():
            player.get_score().set_points(0)
            player.meeples = 7

        self.shuffle_deck(self.shuffle_algo, self.seed)

        for record in past_moves:
            player = self.players.get(record.player_id)
            if player is None:
                continue

            self.board.add_tile_to_board(
                record.move_str,
                self.graph,
                self.tiles_info,
                self.history,
                self.players,
                self.players_order,
                player,
                record_history=False,
            )

        self.current_player_order_list = len(self.history.past_moves) % len(
            self.players_order
        )
        self._ensure_current_player_playable()

    def get_history(self) -> List[str]:
        """Return the current play history."""
        return self.history.list_history()

    def clear_undo_history(self) -> None:
        self.history.clear_future()

    def is_undo_history_empty(self) -> bool:
        return len(self.history.future_moves) == 0

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
        if not self._ensure_current_player_playable():
            return False

        if (
            self.players_order[self.current_player_order_list]
            != self.get_current_player().get_id()
        ):
            print("It is not your turn to play.")
            expected_player = self.players_order[
                self.current_player_order_list
            ]
            print(
                "The one: "
                f"{expected_player} {self.current_player_order_list}. "
                f"You: {self.get_current_player()}"
            )
            turn = max(self.graph.get_verticies().keys(), default=-1) + 1
            print(f"turn:{turn}")
            print(self.players_order)
            return False
        if self.current_hand is None:
            print("Vous devez piocher une tuile avant de jouer.")
            return False

        tile_code = self.extract_tile_code(move)
        if tile_code is not None and tile_code != self.current_hand:
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

        ok = self.rules_manager.check_move(
            move,
            self.graph,
            current_player_id=self.get_current_player().get_id(),
        )
        if ok:
            current_player = self.get_current_player()
            self.board.add_tile_to_board(
                move,
                self.graph,
                self.tiles_info,
                self.history,
                self.players,
                self.players_order,
                current_player,
            )
            print(move + " placed successfully.")
            self.current_hand = None
            self.current_player_order_list = (
                self.current_player_order_list + 1
            ) % self.get_number_of_players()
            self._ensure_current_player_playable()
            """vertices = self.graph.get_verticies()
            for vertex in vertices.values():
                print(vertex.get_neighbors())"""
            return True
        """vertices = self.graph.get_verticies()
        for vertex in vertices.values():
            print(vertex.get_neighbors())
        print('i failed the test')"""
        return False

    def play_ai_turn(self) -> None:
        from .ai_model import RandomPlayer
        from .ai_model import ExpectimaxPlayer
        from .ai_model import MCTSPlayer

        self.tick_blitz()
        if not self._ensure_current_player_playable():
            return
        if not self.get_current_player().is_ai_player():
            return

        ai_player = self.get_current_player()
        print(f"AI Player {ai_player.get_username()} is thinking...")
        self.draw_tile()
        if self.current_hand is None:
            return
        ai_time = self.get_game_configuration().get("ai_time")
        model = None
        move = None
        eval_score = None
        if self.get_game_configuration().get("ai_mode") == "random":
            model = RandomPlayer()
            move = model.random_move(self.current_hand, self)
        elif self.get_game_configuration().get("ai_mode") == "minimax":
            start_time = time.time()
            depth = self.get_game_configuration().get("ai_minimax_depth")
            model = ExpectimaxPlayer(self, start_time, ai_time, depth)
            eval_score, move = model.search(
                self,
                depth=model.depth_max,
                alpha=float("-inf"),
                beta=float("inf"),
                player_to_max=ai_player.get_id(),
                next_player=ai_player.get_id(),
            )
        elif self.get_game_configuration().get("ai_mode") == "mcts":
            start_time = time.time()
            eval_fn_name = self.get_game_configuration().get(
                "ai_mcts_selection"
            )
            model = MCTSPlayer(self, start_time, ai_time, eval_fn_name)
            move = model.mcts(self)
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

    def get_game_configuration(self):
        return self.game_configuration.get_setting()

    def save_config(self) -> None:
        self.game_configuration.save_config()

    def set_game_configuration(self, key: str, value) -> None:
        if key == "timeout":
            key = "time"
        self.game_configuration.settings[key] = value
        if key in ("blitz", "time", "contest_file"):
            self._initialize_mode_state()

    def draw_tile(self) -> str | None:
        timed_out_now = self.tick_blitz()
        if timed_out_now:
            return None
        if not self._ensure_current_player_playable():
            return None

        if self.current_hand is not None:
            return self.current_hand

        tile = self.deck.draw()
        if tile is None:
            return None
        self.current_hand = tile
        return tile

    def end_game(self) -> bool:
        if self._end_game_scored:
            return True
        if self.deck.is_empty() or not self._has_playable_player():
            self.score_manager.score_end_of_game(self.graph, self.players)
            self._end_game_scored = True
            return True
        else:
            return False

    def get_maximum_number_of_players(self) -> int:
        return self.maximum_number_of_players

    def get_minimum_number_of_players(self) -> int:
        return self.minimum_number_of_players

    def get_number_of_players(self) -> int:
        return len(self.players)

    def set_number_of_ai_players(self, num_players: int) -> None:
        self.add_players(num_players)
        self.number_of_ai_players = num_players

    def get_number_of_ai_players(self) -> int:
        return self.number_of_ai_players

    def get_current_player(self) -> Player:
        current_player_id = self.players_order[
            self.current_player_order_list
        ]
        return self.players[current_player_id]

    def save_game_to_file(self, filename: str) -> int:
        return self.save_handler.save_game_to_file(filename)

    def start_load_game(self):
        self.history.clear_history()
        self.graph.reset_graph()
        self.game_repository = GameRepository()
        self.board = Board()
        self.deck = Deck()
        self.current_hand = None
        self.tiles_info = TilesInfo()
        self.rules_manager = RulesManager(self.tiles_info)
        self.current_player_order_list = 0
        self._end_game_scored = False
        self._initialize_mode_state()

    def tick_blitz(self) -> bool:
        return self.game_mode_manager.tick()

    def get_timeout_message(self) -> str:
        return self.game_mode_manager.get_timeout_message()

    def get_current_player_remaining_time_seconds(self) -> float | None:
        return (
            self.game_mode_manager
            .get_current_player_remaining_time_seconds()
        )

    def get_player_remaining_time_seconds(
        self, player_id: int
    ) -> float | None:
        return self.game_mode_manager.get_player_remaining_time_seconds(
            player_id
        )

    def get_all_players_remaining_time_seconds(
        self,
    ) -> list[tuple[int, float]]:
        return self.game_mode_manager.get_all_players_remaining_time_seconds()

    def load_game_from_file(self, filename: str) -> int:
        return self.save_handler.load_game_from_file(filename)

    def rotate_dirs(self, dirs: str | list, rotation: int) -> str | list:
        rotation = rotation % 4
        return dirs[-rotation:] + dirs[:-rotation]

    def generate_tile_ascii(self, vertex: Any) -> list[str]:
        dirs = list(vertex.get_name())  # [N, E, S, W]
        rotation = self.graph.get_vertex_orientation(vertex.get_id())  # 0 à 3
        meeples = self.graph.get_meeples()
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
        vertices = list(self.graph.get_verticies().values())

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
        vertices = self.graph.get_vertices_data()

        return list(vertices.values())

    def get_tile_data(self, tile: int) -> dict | None:
        """
        Retourne une liste exploitable directement par la GUI.
        """
        vertice = self.graph.get_vertice_data(tile)

        return vertice

    def get_meeples_data(self) -> list[dict]:
        """
        Retourne une liste exploitable directement par la GUI.
        """
        meeples = self.graph.get_meeples()

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

    def get_printed_board(self) -> str:
        vertices = list(self.graph.get_verticies().values())

        if not vertices:
            return "No vertices."

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

        TILE_HEIGHT = 3
        EMPTY_TILE = [" " * 9] * TILE_HEIGHT
        board_str = ""
        for row in board:  # chaque ligne de tuiles
            for i in range(TILE_HEIGHT):  # chaque ligne ASCII interne
                board_line = ""
                for tile in row:
                    if tile is None:
                        board_line += EMPTY_TILE[i]
                    else:
                        board_line += tile[i]
                board_str += "   ".join(board_line)
            # espace entre lignes de tuiles
            board_str += "\n"
        return board_str

    def get_close_neighbors(
        self, x: int, y: int
    ) -> tuple[int | None, int | None]:
        return self.graph.find_neighbor_at(x, y)

    def shuffle_deck(self, algo=None, seed=None):
        if algo is None:
            algo = self.shuffle_algo
        if seed is None:
            if self.default_seed is not None:
                seed = self.default_seed
            else:
                seed = Seed().seed
        if algo == "naive":
            self.deck.shuffle_naive(seed)
        else:
            self.deck.shuffle_fisher_yates(seed)
        self.seed = seed
        return seed

    def shuffle_players_order(self) -> None:
        others = [player for player in self.players if player != 0]
        r.shuffle(others)
        self.players_order = [0] + others

    def add_online_players(self, players: list[Player]):
        colors = ["red", "blue", "yellow", "black", "white"]
        for i in range(0, len(players)):
            players[i].set_color(colors[(i - 1) % len(colors)])
            self.players[i] = players[i]

    def add_players(self, nb_players: int) -> None:
        colors = ["red", "blue", "yellow", "black", "white"]
        for i in range(1, nb_players):
            self.players[i] = Player(
                i, f"Player {i}", colors[(i - 2) % len(colors)], True
            )
            self.players_order.append(i)
            self.number_of_ai_players += 1

    def extract_tile_code(self, move):
        try:
            parsed = parse_move(move)
        except ValueError:
            return None

        tile_code = parsed["tile_sides"]
        if parsed.get("center"):
            tile_code = f"{tile_code}/{parsed['center']}"
        return tile_code

    def provide_hint(self) -> str:
        from .ai_model import RandomPlayer
        from .ai_model import ExpectimaxPlayer

        timed_out_now = self.tick_blitz()
        if timed_out_now:
            return ""
        if not self._ensure_current_player_playable():
            return ""

        ai_player = self.get_current_player()
        print(f"AI Player {ai_player.get_username()} is thinking...")
        self.draw_tile()
        if self.current_hand is None:
            return ""
        model = None
        move = ""
        if self.ai_model == "random":
            model = RandomPlayer()
            move = model.random_move(self.current_hand, self)
            print(f"AI Player {ai_player.get_username()} chooses move: {move}")
        elif self.ai_model == "expectimax":
            model = ExpectimaxPlayer(self)
            eval, move = model.search(
                self,
                depth=model.depth_max,
                alpha=float("-inf"),
                beta=float("inf"),
                player_to_max=ai_player.get_id(),
                next_player=ai_player.get_id(),
            )
            print(
                f"AI Player {ai_player.get_username()} chooses move: {move} "
                f"with evaluation score: {eval}"
            )
        # print("main avant de jouer le coup" + self.current_hand)
        return move
