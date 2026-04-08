"""Game state and turn flow for Carcassonne.

This module implements `IGameService`, handling history, undo/redo,
rule checks, and persistence interactions.
"""

import logging
import time
from typing import Any, List

from carcassonne.business_logic.business_logic_factory import (
    BusinessLogicFactory,
)
from carcassonne.interfaces.i_business_logic_factory import (
    IBusinessLogicFactory,
)
from carcassonne.interfaces.i_datas_factory import IDatasFactory
from carcassonne.interfaces.i_game_service import IGameService
from carcassonne.business_logic.game.game_data import GameData
from carcassonne.interfaces.i_graph_data import IGraphData
from carcassonne.business_logic.move_serializer import parse_move
from carcassonne.business_logic.player import Player
from carcassonne.i18n import gettext as _

logger = logging.getLogger(__name__)

OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}
ASCII_TILE_EDGE_WIDTH = 3
ASCII_TILE_CENTER_WIDTH = 7
ASCII_TILE_WIDTH = (
    ASCII_TILE_EDGE_WIDTH * 2 + ASCII_TILE_CENTER_WIDTH
)


class Game(IGameService):

    def __init__(
        self,
        graphData: IGraphData,
        nb_players: int,
        config_overrides=None,
        shuffle_algo: str | None = None,
        default_seed: int | None = None,
        business_logic_factory: IBusinessLogicFactory | None = None,
        datas_factory: IDatasFactory | None = None,
    ) -> None:
        self.business_logic_factory: IBusinessLogicFactory = (
            business_logic_factory or BusinessLogicFactory()
        )
        if datas_factory is None:
            raise ValueError("datas_factory must be provided")
        self.datas_factory: IDatasFactory = datas_factory
        self.game_data = GameData(
            graphData,
            nb_players,
            self.business_logic_factory,
            self.datas_factory,
            config_overrides,
        )
        if shuffle_algo is not None:
            self.game_data.shuffle_algo = shuffle_algo
        if default_seed is not None:
            self.game_data.default_seed = default_seed
        self.save_handler = self.business_logic_factory.create(
            "SaveHandler", self
        )
        self.score_manager = self.business_logic_factory.create("ScoreManager")
        self.blitz_manager = self.business_logic_factory.create(
            "BlitzManager", self.game_data
        )
        self.game_mode_manager = self.business_logic_factory.create(
            "GameModeManager", self.blitz_manager, self
        )
        self.end_game_manager = self.business_logic_factory.create(
            "EndGame",
            self.game_data, self.blitz_manager, self.score_manager
        )
        self.river_manager = self.business_logic_factory.create(
            "RiverManager", self.game_data
        )
        self.deck_manager = self.business_logic_factory.create(
            "DeckManager",
            self.game_data,
            self.blitz_manager,
            self.river_manager,
            self.datas_factory,
        )
        self.undo_redo_manager = self.business_logic_factory.create(
            "UndoRedoManager",
            self.blitz_manager,
            self.deck_manager,
            self.game_data,
            self.datas_factory,
        )
        self.commands = self.business_logic_factory.create(
            "CommandsGame",
            self.blitz_manager, self.deck_manager, self.game_data, self
        )
        self.new_game = self.business_logic_factory.create(
            "NewGame",
            self.river_manager,
            self.deck_manager,
            self.blitz_manager,
            self.game_data,
            self.business_logic_factory,
            self.datas_factory,
            self,
        )
        self.river = None
        _gui_mode = (config_overrides or {}).get("gui", False)
        if self.game_mode_manager.get_mode() != "contest" and not _gui_mode:
            self.start_new_game()

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

    def start_load_game(self):
        self.game_data.start_load_game()
        self.river_manager.reset()

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
        if key in ("blitz", "time", "contest_file"):
            self._initialize_mode_state()

    def get_maximum_number_of_players(self) -> int:
        return self.game_data.get_maximum_number_of_players()

    def get_minimum_number_of_players(self) -> int:
        return self.game_data.get_minimum_number_of_players()

    def get_number_of_players(self) -> int:
        return self.game_data.get_number_of_players()

    def set_number_of_ai_players(self, num_players: int) -> None:
        self.game_data.add_players(num_players)
        self.game_data.number_of_ai_players = num_players

    def adjust_number_of_ai_players(self, num_ai: int) -> None:
        """Adjust AI players to match configuration.

        This replaces any previously set number of AI players with the
        specified count, respecting the maximum players constraint.
        """
        self.game_data.set_number_of_ai_players_configured(num_ai)

    def add_players(self, nb_players: int) -> None:
        self.game_data.add_players(nb_players)

    def get_number_of_ai_players(self) -> int:
        return self.game_data.number_of_ai_players

    def get_players_order(self) -> list[int]:
        return self.game_data.players_order

    def get_current_player(self) -> Player:
        return self.game_data.get_current_player()

    def get_all_players(self) -> list[Player]:
        return list(self.game_data.players.values())

    def save_game_to_file(self, filename: str) -> int:
        return self.save_handler.save_game_to_file(filename)

    def load_game_from_file(self, filename: str) -> int:
        return self.save_handler.load_game_from_file(filename)

    def rotate_dirs(self, dirs: str | list, rotation: int) -> list:
        rotation = rotation % 4
        return dirs[-rotation:] + dirs[:-rotation]

    def generate_tile_ascii(self, vertex: Any) -> list[str]:
        dirs = list(vertex.get_name())  # [N, E, S, W]
        rotation = self.game_data.graph.get_vertex_orientation(
            vertex.get_id()
        )  # 0 to 3
        meeples = self.game_data.graph.get_meeples()
        middle = vertex.get_middle()
        for meeple in meeples:
            if meeple.tile_id != vertex.get_id():
                continue
            pos_label = meeple.get_position_label()
            if pos_label in ["N", "E", "S", "W"]:
                idx = ["N", "E", "S", "W"].index(pos_label)
                dirs[idx] += f"{meeple.player_id}"
            elif pos_label in ["NW", "NE", "SE", "SW"]:
                idx = ["NW", "NE", "SE", "SW"].index(pos_label)
                dirs[idx - 1] += f"/{meeple.player_id}"
            else:
                middle += f"{meeple.player_id}"

        n, e, s, w = self.rotate_dirs(dirs, rotation)
        if middle != "":
            m = f"[{vertex.get_id()}/{middle}]"
        else:
            m = f"[{vertex.get_id()}]"
        space = ASCII_TILE_EDGE_WIDTH * " "

        return [
            space + f"{n:^{ASCII_TILE_CENTER_WIDTH}}" + space,
            f"{w:^{ASCII_TILE_EDGE_WIDTH}}"
            f"{m:^{ASCII_TILE_CENTER_WIDTH}}"
            f"{e:^{ASCII_TILE_EDGE_WIDTH}}",
            space + f"{s:^{ASCII_TILE_CENTER_WIDTH}}" + space,
        ]

    def get_board(self) -> list[Any] | None:
        vertices = list(self.game_data.graph.get_vertices().values())

        if not vertices:
            print(_("No vertices."))
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

        return vertices

    def get_board_data(self) -> list[dict]:
        """
        Return a list directly consumable by the GUI.
        """
        vertices = self.game_data.graph.get_vertices_data()

        return list(vertices.values())

    def get_tile_data(self, tile: str) -> None:
        """
        Return a list directly consumable by the GUI.
        """
        self.game_data.graph.get_vertex_data(tile)

        return None

    def get_meeples_data(self) -> list[dict]:
        """
        Return a list directly consumable by the GUI.
        """
        meeples = self.game_data.graph.get_meeples()

        return [vars(meeple) for meeple in meeples]

    def print_board(self, board: list[list]) -> None:
        TILE_HEIGHT = 3
        EMPTY_TILE = [" " * ASCII_TILE_WIDTH] * TILE_HEIGHT

        for row in board:  # each tile row
            for i in range(TILE_HEIGHT):  # each internal ASCII row
                line = []
                for tile in row:
                    if tile is None:
                        line.append(EMPTY_TILE[i])
                    else:
                        line.append(tile[i])
                print("   ".join(line))
            print()  # spacing between tile rows

    def get_printed_board(self) -> str:
        vertices = list(self.game_data.graph.get_vertices().values())

        if not vertices:
            return "No vertices.\n"

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
        EMPTY_TILE = [" " * ASCII_TILE_WIDTH] * TILE_HEIGHT
        lines: list[str] = []

        for row in board:  # each tile row
            for i in range(TILE_HEIGHT):  # each internal ASCII row
                line = []
                for tile in row:
                    if tile is None:
                        line.append(EMPTY_TILE[i])
                    else:
                        line.append(tile[i])
                lines.append("   ".join(line))
            # spacing between tile rows
            lines.append("")

        return "\n".join(lines)

    def get_close_neighbors(
        self, x: int, y: int
    ) -> tuple[int | None, int | None]:
        return self.game_data.graph.find_neighbor_at(x, y)

    def get_adjacent_position(
        self, vertex_id: int, side: int
    ) -> tuple[int, int] | None:
        return self.game_data.graph.get_adjacent_position(
            vertex_id=vertex_id, side=side
        )

    def start_online_game(self, players: list[Player]):
        return self.new_game.start_online_game(players)

    def add_online_players(self, players: list[Player]) -> None:
        self.game_data.add_online_players(players)

    def draw_tile(self, silent: bool = False) -> str | None:
        return self.deck_manager.draw_tile(silent=silent)

    def shuffle_deck(self, algo=None, seed=None) -> int:
        return self.deck_manager.shuffle_deck(algo, seed)

    def shuffle_players_order(self) -> None:
        self.game_data.shuffle_players_order()

    def extract_tile_code(self, move):
        self.game_data.extract_tile_code(move)

    def parse_move(self, move: str) -> dict:
        return parse_move(move)

    def _connected_components_snapshot(
        self,
    ) -> dict[str, dict[str, list[tuple[int, list[str]]]]]:
        """Build a stable snapshot of terrain connected components.

        Returns:
            A dictionary grouped by terrain type, then by component name.
            Each component contains sorted `(tile_id, direction_group)` pairs.
        """
        if not hasattr(self.game_data.graph, "lands_components"):
            return {}

        snapshot: dict[str, dict[str, list[tuple[int, list[str]]]]] = {}
        for terrain_type in sorted(self.game_data.graph.lands_components):
            components = self.game_data.graph.lands_components[terrain_type]
            snapshot[terrain_type] = {}
            for component_name in sorted(components):
                entries = components[component_name]
                normalized_entries = sorted(
                    (
                        tile_id,
                        sorted(direction_group),
                    )
                    for tile_id, direction_group in entries
                )
                snapshot[terrain_type][component_name] = normalized_entries
        return snapshot

    def _meeples_components_snapshot(self) -> list[dict[str, Any]]:
        """Return a stable view of meeples and their associated component."""
        if not hasattr(self.game_data.graph, "get_meeples"):
            return []

        snapshot: list[dict[str, Any]] = []
        for meeple in self.game_data.graph.get_meeples():
            position_label = meeple.get_position_label()
            snapshot.append(
                {
                    "player_id": getattr(meeple, "player_id", "?"),
                    "tile_id": getattr(meeple, "tile_id", "?"),
                    "position": position_label,
                    "component": getattr(meeple, "lands_components", "?"),
                }
            )

        snapshot.sort(
            key=lambda item: (
                item["player_id"],
                item["tile_id"],
                str(item["position"]),
                str(item["component"]),
            )
        )
        return snapshot

    def _log_rejected_move(self, move: str, reason: str) -> bool:
        gui_mode = False
        try:
            gui_mode = bool(self.get_game_configuration().get("gui"))
        except Exception:
            gui_mode = False
        if gui_mode:
            print(_("{move} failed.").format(move=move), flush=True)
        logger.info(_("Move %s rejected: %s"), move, _(reason))
        return False

    @staticmethod
    def _score_value(player) -> int:
        getter = getattr(player, "get_score_int", None)
        if callable(getter):
            try:
                return int(getter())
            except (TypeError, ValueError):
                pass

        getter = getattr(player, "get_score", None)
        if callable(getter):
            raw_score = getter()
            score_attr = getattr(raw_score, "score", None)
            if isinstance(score_attr, (int, float)):
                return int(score_attr)
            if isinstance(raw_score, (int, float)):
                return int(raw_score)
        return 0

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
            return self._log_rejected_move(move, "blitz timer expired")
        if not self.blitz_manager._ensure_current_player_playable():
            return self._log_rejected_move(
                move, "current player cannot act"
            )
        if (
            self.game_data.players_order[
                self.game_data.current_player_order_list
            ]
            != self.get_current_player().get_id()
        ):
            print(_("It is not your turn to play."))
            expected_player = self.game_data.players_order[
                self.game_data.current_player_order_list
            ]
            print(
                _(
                    "Expected player: {expected_player} at index "
                    "{current_index}. Current player: {current_player}"
                ).format(
                    expected_player=expected_player,
                    current_index=self.game_data.current_player_order_list,
                    current_player=self.get_current_player(),
                )
            )
            turn = (
                max(self.game_data.graph.get_vertices().keys(), default=-1)
                + 1
            )
            print(_("turn: {turn}").format(turn=turn))
            print(self.game_data.players_order)
            return self._log_rejected_move(
                move, "it is not this player's turn"
            )
        if self.game_data.current_hand is None:
            print(_("You must draw a tile before you can play it."))
            return self._log_rejected_move(
                move, "no tile is currently in hand"
            )

        tile_code = self.game_data.extract_tile_code(move)
        if tile_code is not None and tile_code != self.game_data.current_hand:
            print(
                _("You must play the tile in hand: {hand}").format(
                    hand=self.game_data.current_hand
                )
            )
            return self._log_rejected_move(
                move,
                _(
                    "tile in hand is {current_hand}, not {tile_code}"
                ).format(
                    current_hand=self.game_data.current_hand,
                    tile_code=tile_code,
                )
            )

        try:
            parsed_move = parse_move(move)
        except ValueError:
            return self._log_rejected_move(move, "move format is invalid")
        current_player_meeples = self.get_current_player().get_meeples()
        if parsed_move.get("meeple") and current_player_meeples <= 0:
            print(_("No meeple remaining."))
            return self._log_rejected_move(move, "no meeple remaining")

        ok = self.game_data.rules_manager.check_move(
            move,
            self.game_data.graph,
            self.river_manager,
            current_player_id=self.get_current_player().get_id(),
        )
        if not ok:
            explain_reason = "move validation failed"
            if hasattr(self.game_data.rules_manager, "explain_invalid_move"):
                explain_reason = (
                    self.game_data.rules_manager.explain_invalid_move(
                        move,
                        self.game_data.graph,
                        self.river_manager,
                        current_player_id=self.get_current_player().get_id(),
                    )
                )
            return self._log_rejected_move(move, explain_reason)

        current_player = self.get_current_player()

        previous_scores = {
            player_id: self._score_value(player)
            for player_id, player in self.game_data.players.items()
        }
        self.game_data.board.add_tile_to_board(
            move,
            self.game_data.graph,
            self.game_data.tiles_info,
            self.game_data.history,
            self.game_data.players,
            self.game_data.players_order,
            current_player,
        )
        print(_("{move} placed successfully.").format(move=move), flush=True)
        turn = max(
            self.game_data.graph.get_vertices().keys(), default=-1
        )
        tile_code = self.game_data.current_hand or "?"
        logger.info(
            _("Turn %d: Player %s places tile %s"),
            turn,
            current_player.get_id(),
            tile_code,
        )
        tile_added_log = (
            self.game_data.board.consume_last_tile_added_log_info()
        )
        if tile_added_log is not None:
            logger.debug(
                _("Tile %d (%s) added at position %s"),
                tile_added_log[0],
                tile_added_log[1],
                tile_added_log[2],
            )
        scoring_events = self.game_data.board.consume_last_scoring_log_events()
        meeple_log = self.game_data.board.consume_last_meeple_log_info()
        if meeple_log is not None:
            logger.info(
                _("Player %d places meeple at %s on component %s"),
                meeple_log[0],
                meeple_log[1],
                meeple_log[2],
            )
        for event_type, payload in scoring_events:
            if event_type == "component_completed":
                logger.info(
                    _("Component %s (%s) completed and scored"),
                    payload["name"],
                    payload["terrain"],
                )
            elif event_type == "meeple_returned":
                logger.info(
                    _("Player %d gets back %d meeple(s) from component %s"),
                    payload["player_id"],
                    payload["count"],
                    payload["component"],
                )
        for player_id in self.game_data.players_order:
            player = self.game_data.players[player_id]
            old_score = previous_scores.get(player_id, 0)
            new_score = self._score_value(player)
            if new_score != old_score:
                logger.info(
                    _("Player %d score updated: %d -> %d (%+d)"),
                    player_id,
                    old_score,
                    new_score,
                    new_score - old_score,
                )
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(
                _("Connected terrain components: %s"),
                self._connected_components_snapshot(),
            )
            logger.debug(
                _("Meeples and associated components: %s"),
                self._meeples_components_snapshot(),
            )
        self.river_manager.update_river_turn(move.split("/"))
        self.game_data.current_hand = None
        self.game_data.current_player_order_list = (
            self.game_data.current_player_order_list + 1
        ) % self.get_number_of_players()
        self.blitz_manager._ensure_current_player_playable()
        return True

    def play_ai_turn(self, game=None) -> None:
        from carcassonne.business_logic.ai_model import RandomPlayer
        from carcassonne.business_logic.ai_model import ExpectimaxPlayer
        from carcassonne.business_logic.ai_model import (
            IterativeDeepeningPlayer,
        )
        from carcassonne.business_logic.ai_model import MCTSPlayer

        if game is None:
            raise ValueError("game parameter is required for play_ai_turn")

        self.tick_blitz()
        if not self.blitz_manager._ensure_current_player_playable():
            return
        if self.end_game():
            return
        if not self.get_current_player().is_ai_player():
            return

        ai_player = self.get_current_player()
        print(
            _("AI Player {player} is thinking...").format(
                player=ai_player.get_username()
            )
        )
        self.deck_manager.draw_tile(silent=True)
        if self.game_data.current_hand is None:
            self.end_game()
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
            eval_name = self.get_game_configuration().get(
                "ai_minimax_scoring", "baseline"
            )
            model = ExpectimaxPlayer(
                game,
                start_time,
                ai_time or 10.0,
                depth or 5,
                eval_name=eval_name,
            )
            eval_score, move = model.search(
                game,
                depth=model.depth_max,
                alpha=float("-inf"),
                beta=float("inf"),
                player_to_max=ai_player.get_id(),
                next_player=ai_player.get_id(),
            )
        elif self.get_game_configuration().get("ai_mode") == "iterative":
            start_time = time.time()
            depth = self.get_game_configuration().get("ai_minimax_depth", 5)
            eval_name = self.get_game_configuration().get(
                "ai_minimax_scoring", "baseline"
            )
            model = IterativeDeepeningPlayer(
                game,
                start_time,
                ai_time or 10.0,
                depth or 5,
                eval_name=eval_name,
            )
            eval_score, move = model.search(
                game,
                alpha=float("-inf"),
                beta=float("inf"),
                player_to_max=ai_player.get_id(),
                next_player=ai_player.get_id(),
            )
        elif self.get_game_configuration().get("ai_mode") == "mcts":
            start_time = time.time()
            eval_fn_name = self.get_game_configuration().get(
                "ai_mcts_selection", "UCT"
            )
            model = MCTSPlayer(
                game, start_time, ai_time or 10.0, eval_fn_name or "UCT"
            )
            move = model.mcts(game)
        if not move:
            print(
                _("AI Player {player} has no legal move.").format(
                    player=ai_player.get_username()
                )
            )
            print(self.game_data.current_hand)
            return

        # Validate move format: TILE/POSITION or TILE/POSITION/MEEPLE.
        if "/" not in str(move):
            print(
                _(
                    "AI move '{move}' is malformed (missing position). "
                    "Skipping this turn."
                ).format(move=move)
            )
            # Force change to next player to avoid infinite loop
            self.game_data.current_player_order_list = (
                self.game_data.current_player_order_list + 1
            ) % self.get_number_of_players()
            return

        if eval_score is None:
            print(
                _("AI Player {player} chooses move: {move}").format(
                    player=ai_player.get_username(),
                    move=move,
                )
            )
        else:
            print(
                _(
                    "AI Player {player} chooses move: {move} "
                    "with evaluation score: {score}"
                ).format(
                    player=ai_player.get_username(),
                    move=move,
                    score=eval_score,
                )
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
                    _(
                        "AI move rejected (no meeples left). "
                        "Retrying without meeple: {fallback_move}"
                    ).format(fallback_move=fallback_move)
                )
                fallback_played = self.play_move(fallback_move)

            if not fallback_played:
                print(
                    _(
                        "AI Player {player} produced an invalid move: {move}"
                    ).format(
                        player=ai_player.get_username(),
                        move=move,
                    )
                )
                # Force change to next player to avoid infinite loop
                self.game_data.current_player_order_list = (
                    self.game_data.current_player_order_list + 1
                ) % self.get_number_of_players()
                return

    def start_new_game(
        self, players_order: list[int] | None = None, seed: int | None = None
    ) -> None:
        return self.new_game.start_new_game(players_order, seed)

    def end_game(self) -> bool:
        return self.end_game_manager.end_game()

    def get_winners(self) -> list[Player]:
        return self.end_game_manager.get_winners()

    def get_winner(self) -> Player | None:
        return self.end_game_manager.get_winner()

    def is_draw(self) -> bool:
        return self.end_game_manager.is_draw()

    def undo(self) -> None:
        self.undo_redo_manager.undo()

    def redo(self) -> None:
        self.undo_redo_manager.redo()

    def provide_hint(self) -> str:
        return self.commands.provide_hint()

    def get_all_players_remaining_time_seconds(
        self,
    ) -> List[tuple[int, float]]:
        return self.blitz_manager.get_all_players_remaining_time_seconds()

    def get_current_player_remaining_time_seconds(self) -> float | None:
        return self.blitz_manager.get_player_remaining_time_seconds(
            self.game_data.get_current_player().get_id()
        )

    def get_player_remaining_time_seconds(
        self, player_id: int
    ) -> float | None:
        return self.blitz_manager.get_player_remaining_time_seconds(player_id)

    def tick_blitz(self) -> bool:
        return self.blitz_manager.tick_blitz()

    def get_timeout_message(self) -> str:
        return self.blitz_manager.get_timeout_message()
