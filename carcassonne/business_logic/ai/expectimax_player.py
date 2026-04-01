"""Expectimax AI player with iterative deepening."""

from __future__ import annotations

import copy
import time
from typing import List, Tuple, TYPE_CHECKING

from carcassonne.business_logic.interfaces.i_graph_data import IGraphData
from carcassonne.business_logic.interfaces.i_tiles_info import ITilesInfo
from carcassonne.datas.serializer import build_str, parse_move
from carcassonne.business_logic.heuristic import (
    evaluate_state as heuristic_evaluate_state,
)
from carcassonne.business_logic.heuristic_short_term import (
    evaluate_state as short_term_evaluate_state,
)
from carcassonne.business_logic.heuristic_disruption import (
    evaluate_state as disruption_evaluate_state,
)

if TYPE_CHECKING:
    from carcassonne.business_logic.game.game import Game


class ExpectimaxPlayer:
    """
    AI player using Expectimax pruning
    for intelligent move selection.
    """

    L = -100  # Should be minimum of evaluation function
    U = 100  # Should be maximum of evaluation function

    # Example positions for meeple placement
    meeple_placement_list = ["NW", "N", "NE", "E", "SE", "S", "SW", "W", "C"]

    def __init__(
        self,
        game: "Game",
        start_time: float,
        max_time: float,
        depth: int,
        is_maximizing: bool = True,
        eval_name: str = "",
        eval_fn=None,
        preferred_root_move: str | None = None,
        history_table: dict[str, int] | None = None,
        prefer_root_meeple: bool = False,
    ):
        """
        Initialize the Expectimax AI player.

        Args:
            depth: Maximum depth for the search tree (default: 4)
            is_maximizing: Whether player maximizes
                (True for AI, False for opponent)
        """
        self.game = game
        self.depth = depth
        self.is_maximizing = is_maximizing
        self.nodes_explored = 0
        # Stack used to save/restore scoring state around each simulation step
        self._sim_state_stack = []
        # evaluation function (callable(graph, ai_score, opponent_score) ->
        # float)
        if eval_fn is not None:
            self.eval_fn = eval_fn
        else:
            self.set_evaluation_method(eval_name)
        self.depth_max = depth
        self.start_time = start_time
        self.max_time = max_time
        self.preferred_root_move = preferred_root_move
        self.prefer_root_meeple = prefer_root_meeple
        # Shared between iterative-deepening iterations to improve move order.
        self.history_table = history_table if history_table is not None else {}

    def _time_exceeded(self) -> bool:
        return time.time() - self.start_time > self.max_time

    def set_evaluation_method(self, name_or_fn):
        """Set evaluation by name or by callable.

        Accepts a callable(graph, ai_score, opponent_score) or a string name.
        """
        if callable(name_or_fn):
            self.eval_fn = name_or_fn
            return

        evaluations = {
            "": heuristic_evaluate_state,
            "BASELINE": heuristic_evaluate_state,
            "SHORT_TERM": short_term_evaluate_state,
            "DISRUPTION": disruption_evaluate_state,
        }

        name = (name_or_fn or "").upper()
        if name in evaluations:
            self.eval_fn = evaluations[name]
            return

        raise ValueError(f"Unknown evaluation method: {name_or_fn}")

    def get_possible_moves(self, tile: str, game: "Game") -> List[str]:
        """
        Generate all legal moves from the current game state.

        Args:
            graph: The game board graph
            tiles_info: Information about available tiles
            rules_manager: Manager for game rules

        Returns:
            List of possible moves as strings
        """
        possible_moves = []

        # Try to place each available tile on each empty neighbor position
        vertices = copy.deepcopy(game.game_data.graph.get_verticies())
        can_place_meeple = (
            game.game_data.get_current_player().get_meeples() > 0
        )
        meeple_indices = (
            range(-1, len(self.meeple_placement_list))
            if can_place_meeple
            else (-1,)
        )

        # Try to place the tile next to each existing vertex
        for vertex_id, vertex in vertices.items():
            # Try each direction (North, South, East, West)
            for direction in ["N", "S", "E", "W"]:
                # Check if this side is free
                if vertex.is_neighbor_free(
                    game.game_data.tiles_info.direction_dict.get(direction, 0)
                ):
                    # Try each rotation (0, 90, 180, 270 degrees)
                    for rotation in range(4):
                        # -1 means no meeple placement
                        for meeple in meeple_indices:
                            if meeple == -1:
                                move = (
                                    f"{tile}/{vertex_id}{direction}{rotation}"
                                )
                            else:
                                move = (
                                    f"{tile}/{vertex_id}{direction}{rotation}/"
                                    f"{self.meeple_placement_list[meeple]}"
                                )
                            # Verify the move is legal
                            id_player = (
                                game.game_data.get_current_player().get_id()
                            )
                            if game.game_data.rules_manager.check_move(
                                move,
                                game.game_data.graph,
                                game.river_manager,
                                current_player_id=id_player,
                            ):
                                possible_moves.append(move)

        return possible_moves

    def _order_moves(self, moves: List[str], depth: int) -> List[str]:
        """Order candidate moves to improve pruning efficiency.

        Priority:
        1) Root preferred move from previous iterative-deepening pass.
        2) History heuristic score (higher first).
        """
        if not moves:
            return moves

        preferred = None
        if depth == self.depth_max:
            preferred = self.preferred_root_move

        def _has_meeple(move: str) -> int:
            if not (self.prefer_root_meeple and depth == self.depth_max):
                return 0
            try:
                parsed = parse_move(move)
            except ValueError:
                return 0
            return 1 if parsed.get("meeple") else 0

        def _score(move: str) -> tuple[int, int]:
            is_preferred = 1 if preferred and move == preferred else 0
            history_score = self.history_table.get(move, 0)
            meeple_score = _has_meeple(move)
            return (is_preferred, meeple_score, history_score)

        return sorted(moves, key=_score, reverse=True)

    def search(
        self,
        game: "Game",
        depth: int,
        alpha: float,
        beta: float,
        player_to_max: int,
        next_player: int,
    ) -> Tuple[float, str]:
        """Recursive search function for Expectimax algorithm.
        Adapt between Max and Min nodes based on the player parameter."""
        check_time = self._time_exceeded()
        if (
            self.terminal(game.game_data.tiles_info)
            or depth == 0
            or check_time
        ):
            return self.eval_fn(game, player_to_max, next_player), ""
        restored_hand = game.game_data.current_hand
        best_move = ""
        if player_to_max == next_player:  # Max node
            max_eval = float("-inf")
            possible_moves = self.get_possible_moves(
                game.game_data.current_hand, game
            )
            if not possible_moves:
                return self.eval_fn(game, player_to_max, next_player), ""
            ordered_moves = self._order_moves(possible_moves, depth)
            for move in ordered_moves:
                res = self.play_move_for_ai(game, move)
                if not res:
                    print("SEARCH MAX DIDNT WORK")
                    continue
                eval_score = self.star25(
                    game,
                    depth - 1,
                    alpha,
                    beta,
                    player_to_max,
                    (next_player + 1) % len(game.game_data.players),
                )

                self.undo_for_ai(game)
                # print("Move undone")
                # game.get_board()
                game.game_data.current_hand = restored_hand
                if eval_score > max_eval and depth == self.depth_max:
                    best_move = move
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                check_time = self._time_exceeded()
                if beta <= alpha or check_time:
                    self.history_table[move] = (
                        self.history_table.get(move, 0) + depth * depth
                    )
                    break
            return max_eval, best_move
        else:  # Min node (opponent's turn)
            min_eval = float("inf")
            possible_moves = self.get_possible_moves(
                game.game_data.current_hand, game
            )
            if not possible_moves:
                return self.eval_fn(game, player_to_max, next_player), ""
            ordered_moves = self._order_moves(possible_moves, depth)
            for move in ordered_moves:
                res = self.play_move_for_ai(game, move)
                if not res:
                    print("SEARCH MIN DIDNT WORK")
                    game.get_board()
                    print(move)
                    continue
                eval_score = self.star25(
                    game,
                    depth - 1,
                    alpha,
                    beta,
                    player_to_max,
                    (next_player + 1) % len(game.game_data.players),
                )

                self.undo_for_ai(game)
                # print("Move undone")
                game.game_data.current_hand = restored_hand
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                check_time = self._time_exceeded()
                if beta <= alpha or check_time:
                    self.history_table[move] = (
                        self.history_table.get(move, 0) + depth * depth
                    )
                    break
            return min_eval, ""

    def event_prob(self, graph: IGraphData, tile: str, N: dict) -> float:
        """Calculate the probability of a chance event (tile draw)."""
        total_tiles_left = sum(N.values())
        if total_tiles_left == 0:
            return 0.0
        return N.get(tile) / total_tiles_left

    def n_probe(
        self,
        game: "Game",
        alpha: float,
        beta: float,
        depth: int,
        player_to_max: int,
        next_player: int,
        probingFactor: int = 1,
    ) -> float:

        moves = self.get_possible_moves(game.game_data.current_hand, game)
        if not moves:
            return self.eval_fn(game, player_to_max, next_player)
        moves = self._order_moves(moves, depth)

        # ordonner les moves selon un heuristique rapide à calculer
        # moves = sorted(
        #     moves,
        #     key=lambda m: self.quick_eval_move(game, m, player_to_max),
        #     reverse=True,
        # )

        best = alpha
        explored_move = False

        restored_hand = game.game_data.current_hand

        for i in range(min(probingFactor, len(moves))):
            if self._time_exceeded():
                return (
                    best
                    if explored_move
                    else self.eval_fn(game, player_to_max, next_player)
                )
            move = moves[i]

            if not self.play_move_for_ai(game, move):
                continue
            explored_move = True

            value = self.star25(
                game,
                depth - 1,
                best,
                beta,
                player_to_max,
                (next_player + 1) % len(game.game_data.players),
            )

            self.undo_for_ai(game)
            game.game_data.current_hand = restored_hand

            if value >= beta:
                return beta

            if value > best:
                best = value

        return best

    def apply_chance_event(self, game: "Game", tile: str) -> None:
        """Apply a chance event (e.g., drawing a tile) to the game state."""
        # TODO: Make the next tile to draw the tile parameter
        game.game_data.current_hand = tile
        # TODO: bug with river tiles when they are commented out in the deck.
        # game.deck.tiles.remove(tile)

    def num_successors(self, tiles_info: ITilesInfo) -> dict:
        """Return the number of possible chance events from this state."""
        N = {}
        for tile, tile_nb in tiles_info.tiles_count.items():
            if tile_nb > 0:
                N[tile] = tile_nb
        return N

    def terminal(self, tiles_info: ITilesInfo) -> bool:
        """Check if the game is in a terminal state (no more moves)."""
        # This is a simplified check - you should implement this based on your
        # game rules

        # If no more tiles are available, the game is terminal
        total_tiles = sum(tiles_info.tiles_count.values())
        if total_tiles == 0:
            return True

        return False

    def star25(
        self,
        game: "Game",
        depth: int,
        alpha: float,
        beta: float,
        player_to_max: int,
        next_player: int,
    ) -> float:
        check_time = self._time_exceeded()
        if (
            self.terminal(game.game_data.tiles_info)
            or depth == 0
            or check_time
        ):
            return self.eval_fn(game, player_to_max, next_player)

        successors = self.num_successors(game.game_data.tiles_info)
        if not successors:
            return self.eval_fn(game, player_to_max, next_player)

        total_tiles = sum(successors.values())
        if total_tiles <= 0:
            return self.eval_fn(game, player_to_max, next_player)

        # probabilités
        probs = {
            tile: count / total_tiles for tile, count in successors.items()
        }
        probs = dict(sorted(probs.items(), key=lambda x: -x[1]))

        cur_x = 0
        cur_y = 1
        probe_bounds = {}
        restored_hand = game.game_data.current_hand
        fallback_value = self.eval_fn(game, player_to_max, next_player)

        # ---------- PROBING PHASE ----------
        for tile, prob in probs.items():
            if self._time_exceeded():
                game.game_data.current_hand = restored_hand
                return cur_x + cur_y * fallback_value

            cur_y -= prob

            cur_beta = (beta - self.L * cur_y - cur_x) / prob

            self.apply_chance_event(game, tile)

            value = self.n_probe(
                game,
                alpha,
                cur_beta,
                depth - 1,
                player_to_max,
                next_player,
            )
            game.game_data.current_hand = restored_hand

            probe_bounds[tile] = value

            if value >= cur_beta:
                game.game_data.current_hand = restored_hand
                return beta

            cur_x += prob * value

        # ---------- SEARCH PHASE ----------
        cur_x = 0
        cur_y = 1

        for tile, prob in probs.items():
            if self._time_exceeded():
                game.game_data.current_hand = restored_hand
                return cur_x + cur_y * fallback_value

            cur_y -= prob

            cur_alpha = (alpha - cur_x - self.U * cur_y) / prob
            cur_beta = (beta - cur_x - self.L * cur_y) / prob

            ax = max(self.L, cur_alpha, probe_bounds.get(tile, self.L))
            bx = min(self.U, cur_beta)

            self.apply_chance_event(game, tile)

            value, _ = self.search(
                game, depth - 1, ax, bx, player_to_max, next_player
            )
            game.game_data.current_hand = restored_hand

            if value >= cur_beta:
                game.game_data.current_hand = restored_hand
                return beta

            if value <= cur_alpha:
                game.game_data.current_hand = restored_hand
                return alpha

            if self._time_exceeded():
                break

            cur_x += prob * value

        game.game_data.current_hand = restored_hand
        return cur_x

    def undo_for_ai(self, game: "Game") -> None:
        """Undo the last AI move."""
        if game.game_data.history.past_moves:
            previous_play = game.game_data.history.pop_past()
            game.game_data.board.remove_tile_from_board(
                build_str(previous_play),
                game.game_data.graph,
                game.game_data.tiles_info,
                game.game_data.history,
                players=game.game_data.players,
            )
            game.game_data.current_player_order_list = (
                game.game_data.current_player_order_list - 1
            ) % game.game_data.get_number_of_players()
            # Restore player scores, meeple counts and scored_components to
            # their exact state before this simulation step so that AI
            # exploration never permanently modifies the real game state.
            if self._sim_state_stack:
                (
                    saved_scores,
                    saved_meeples,
                    saved_scored,
                    saved_lands_components,
                    saved_next_set_id,
                ) = self._sim_state_stack.pop()
                for pid, score in saved_scores.items():
                    game.game_data.players[pid].get_score().set_points(score)
                for pid, meeples in saved_meeples.items():
                    game.game_data.players[pid].meeples = meeples
                game.game_data.board.scored_components = saved_scored
                game.game_data.graph.lands_components = saved_lands_components
                game.game_data.graph.next_set_id = saved_next_set_id

    def play_move_for_ai(self, game: "Game", move: str) -> None:
        """Play move for AI exploring the possibilities."""
        tile_code = game.game_data.extract_tile_code(move)
        if tile_code is not None and tile_code != game.game_data.current_hand:
            hand = game.game_data.current_hand
            print(f"Vous devez jouer la tuile en main: {hand}")
            return False

        ok = game.game_data.rules_manager.check_move(
            move,
            game.game_data.graph,
            game.river_manager,
            current_player_id=game.game_data.get_current_player().get_id(),
        )
        if ok:
            # Snapshot scoring state before modifying it so undo_for_ai can
            # fully restore the real game state.
            saved_scores = {
                pid: p.get_score_int()
                for pid, p in game.game_data.players.items()
            }
            saved_meeples = {
                pid: p.get_meeples()
                for pid, p in game.game_data.players.items()
            }
            saved_scored = set(game.game_data.board.scored_components)
            saved_lands_components = copy.deepcopy(
                game.game_data.graph.lands_components
            )
            saved_next_set_id = copy.deepcopy(game.game_data.graph.next_set_id)
            game.game_data.board.add_tile_to_board(
                move,
                game.game_data.graph,
                game.game_data.tiles_info,
                game.game_data.history,
                game.game_data.players,
                game.game_data.players_order,
                game.game_data.get_current_player(),
            )
            game.game_data.current_hand = None
            game.game_data.current_player_order_list = (
                game.game_data.current_player_order_list + 1
            ) % game.game_data.get_number_of_players()
            self._sim_state_stack.append(
                (
                    saved_scores,
                    saved_meeples,
                    saved_scored,
                    saved_lands_components,
                    saved_next_set_id,
                )
            )
            return True
        return False


class IterativeDeepeningPlayer:
    """Iterative deepening wrapper around Expectimax/Minimax search."""

    def __init__(
        self,
        game: "Game",
        start_time: float,
        max_time: float,
        max_depth: int,
        eval_name: str = "",
        eval_fn=None,
    ):
        self.game = game
        self.start_time = start_time
        self.max_time = max_time
        self.max_depth = max(1, int(max_depth or 1))
        self.eval_name = eval_name
        self.eval_fn = eval_fn
        self.last_completed_depth = 0
        self.history_table: dict[str, int] = {}

    def _time_exceeded(self) -> bool:
        return time.time() - self.start_time > self.max_time

    def search(
        self,
        game: "Game",
        alpha: float,
        beta: float,
        player_to_max: int,
        next_player: int,
    ) -> Tuple[float, str]:
        """Run deepening iterations and keep the best fully-searched move."""
        best_eval = float("-inf")
        best_move = ""
        preferred_move = ""

        for depth in range(1, self.max_depth + 1):
            if self._time_exceeded():
                break

            solver = ExpectimaxPlayer(
                game,
                self.start_time,
                self.max_time,
                depth,
                eval_name=self.eval_name,
                eval_fn=self.eval_fn,
                preferred_root_move=preferred_move,
                history_table=self.history_table,
            )

            eval_score, move = solver.search(
                game,
                depth=depth,
                alpha=alpha,
                beta=beta,
                player_to_max=player_to_max,
                next_player=next_player,
            )

            if self._time_exceeded() and not move:
                break

            self.last_completed_depth = depth
            if move:
                best_eval = eval_score
                best_move = move
                preferred_move = move
                self.history_table[move] = (
                    self.history_table.get(move, 0) + depth * depth
                )

        return best_eval, best_move
