"""
This module implements the AI player using the Expectimax pruning algorithm.
It provides intelligent move selection for the AI player in Carcassonne.
"""
import math
import random
import time
from typing import List, Tuple, Optional, TYPE_CHECKING

from carcassonne.datas.history import MoveRecord
from carcassonne.business_logic.interfaces.i_graph_data import IGraphData
from carcassonne.business_logic.interfaces.i_tiles_info import ITilesInfo
from carcassonne.business_logic.rules_manager import RulesManager

from carcassonne.datas.serializer import build_str

if TYPE_CHECKING:
    from carcassonne.business_logic.game.game import Game
from carcassonne.business_logic.heuristic import (
    evaluate_state as heuristic_evaluate_state,
)

import copy


def _is_river_tile(tile: str | None) -> bool:
    """Return True when a tile belongs to the river deck."""
    return bool(tile) and "S" in tile


def _discard_unplayable_tile(game: "Game", tile: str | None) -> None:
    """Put an unplayable tile back at the bottom of its source deck."""
    if tile is None:
        return
    if _is_river_tile(tile):
        game.game_data.deck.river_tiles.append(tile)
    else:
        game.game_data.deck.append(tile)


def _restore_drawn_tile_after_undo(game: "Game", tile: str | None) -> None:
    """Restore a drawn tile to the top of its source deck for undo."""
    if tile is None:
        return
    if _is_river_tile(tile):
        game.game_data.deck.river_tiles.insert(0, tile)
    else:
        game.game_data.deck.tiles.append(tile)


class RandomPlayer:

    # Example positions for meeple placement
    meeple_placement_list = ["NW", "N", "NE", "E", "SE", "S", "SW", "W", "C"]

    def get_possible_moves(self, tile, game: "Game") -> List[str]:
        """
        Generate all legal moves from the current game state.

        Args:
            graph: The game board graph
            rules_manager: Manager for game rules

        Returns:
            List of possible moves as strings
        """
        possible_moves = []

        # Try to place each available tile on each empty neighbor position
        vertices = game.game_data.graph.get_verticies()
        can_place_meeple = game.game_data.get_current_player().get_meeples() > 0
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
                            id_player = game.game_data.get_current_player().get_id()
                            if game.game_data.rules_manager.check_move(
                                move,
                                game.game_data.graph,
                                game.river_manager,
                                current_player_id=id_player,
                            ):
                                possible_moves.append(move)
        return possible_moves

    def random_move(self, tile, game: "Game") -> str:
        """Select a random move from the list of possible moves."""
        import random as r

        possible_moves = self.get_possible_moves(tile, game)

        return r.choice(possible_moves) if possible_moves else ''


class ExpectimaxPlayer:
    """
    AI player using Expectimax pruning
    for intelligent move selection.
    """

    L = -100  # Should be minimum of evaluation function
    U = 100  # Should be maximum of evaluation function

    # Example positions for meeple placement
    meeple_placement_list = ["NW", "N", "NE", "E", "SE", "S", "SW", "W", "C"]

    def __init__(self, game: 'Game', start_time: float, max_time: float,
                 depth: int, is_maximizing: bool = True,
                 eval_name: str = "", eval_fn=None):
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

    def _time_exceeded(self) -> bool:
        return time.time() - self.start_time > self.max_time

    def set_evaluation_method(self, name_or_fn):
        """Set evaluation by name or by callable.

        Accepts a callable(graph, ai_score, opponent_score) or a string name.
        """
        if callable(name_or_fn):
            self.eval_fn = name_or_fn
            return

        name = (name_or_fn or "").upper()
        if name == "":
            self.eval_fn = heuristic_evaluate_state
        else:
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
        can_place_meeple = game.game_data.get_current_player().get_meeples() > 0
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
                            id_player = game.game_data.get_current_player().get_id()
                            if game.game_data.rules_manager.check_move(
                                move,
                                game.game_data.graph,
                                game.river_manager,
                                current_player_id=id_player,
                            ):
                                possible_moves.append(move)

        return possible_moves

    def search(self, game: 'Game', depth: int, alpha: float, beta: float,
               player_to_max: int, next_player: int) -> Tuple[float, str]:
        """Recursive search function for Expectimax algorithm.
        Adapt between Max and Min nodes based on the player parameter."""
        check_time = self._time_exceeded()
        if self.terminal(
                game.game_data.tiles_info) or depth == 0 or check_time:
            return self.eval_fn(game, player_to_max, next_player), ''
        restored_hand = game.game_data.current_hand
        best_move = ""
        if player_to_max == next_player:  # Max node
            max_eval = float("-inf")
            possible_moves = self.get_possible_moves(
                game.game_data.current_hand, game)
            if not possible_moves:
                return self.eval_fn(game, player_to_max, next_player), ""
            for move in possible_moves:
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
                    break
            return max_eval, best_move
        else:  # Min node (opponent's turn)
            min_eval = float("inf")
            possible_moves = self.get_possible_moves(
                game.game_data.current_hand, game)
            if not possible_moves:
                return self.eval_fn(game, player_to_max, next_player), ""
            for move in possible_moves:
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

            self.play_move_for_ai(game, move)
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
        if self.terminal(
                game.game_data.tiles_info) or depth == 0 or check_time:
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

    def undo_for_ai(self, game: 'Game') -> None:
        """Undo the last AI move."""
        if game.game_data.history.past_moves:
            previous_play = game.game_data.history.pop_past()
            game.game_data.history.push_future(previous_play)
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
            _restore_drawn_tile_after_undo(
                game,
                previous_play.move_str.split("/")[0],
            )
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
                ) = (
                    self._sim_state_stack.pop()
                )
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
            print(
                f"Vous devez jouer la tuile en main: {game.game_data.current_hand}")
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
                pid: p.get_score_int() for pid,
                p in game.game_data.players.items()}
            saved_meeples = {
                pid: p.get_meeples() for pid,
                p in game.game_data.players.items()}
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


class MCTSNode:
    def __init__(self, game: 'Game', mcts_player: 'MCTSPlayer',
                 parent=None, move=None, player=None):
        self.state = game
        self.parent = parent
        self.move = move  # coup qui mène à ce noeud
        self.player = player  # joueur qui a joué ce coup
        self.mcts_player = mcts_player

        self.children = []
        self.untried_moves = mcts_player.get_possible_moves(
            game.game_data.current_hand, game)

        self.visits = 0
        self.total_reward = 0.0  # somme des récompenses

    def get_state(self):
        return self.state

    def get_parent(self):
        return self.parent

    def get_move(self):
        return self.move

    def get_player(self):
        return self.player

    def get_children(self):
        return self.children

    def get_untried_moves(self):
        return self.untried_moves

    def get_visits(self):
        return self.visits

    def get_total_reward(self):
        return self.total_reward

    def add_visitor(self, number):
        self.visits += number

    def add_reward(self, reward):
        self.total_reward += reward


class MCTSPlayer:

    # Example positions for meeple placement
    meeple_placement_list = ['NW', 'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'C']

    def __init__(self, game: 'Game', start_time: float, max_time: float,
                 eval_name: str = "", eval_fn=None):
        """
        Initialize the Expectimax AI player.

        Args:
            depth: Maximum depth for the search tree (default: 4)
            is_maximizing: Whether this player is maximizing (True for AI,
              False for opponent)
        """
        self.game = game
        self.nodes_explored = 0
        # evaluation function (callable(graph, ai_score, opponent_score)
        #  -> float)
        if eval_fn is not None:
            self.eval_fn = eval_fn
        else:
            self.set_evaluation_method(eval_name)
        self.start_time = start_time
        self.max_time = max_time
        self.end_time = self.start_time + self.max_time
        # Stack used to save/restore scoring state around each simulation step
        self._sim_state_stack = []

    def set_evaluation_method(self, name_or_fn):
        """Set evaluation by name or by callable.

        Accepts a callable(graph, ai_score, opponent_score) or a string name.
        """
        if name_or_fn == "UCT":
            name_or_fn = self.uct_select_child
            self.eval_fn = name_or_fn
            return
        if callable(name_or_fn):
            self.eval_fn = name_or_fn
            return

        name = (name_or_fn or '').upper()
        if name == '':
            # default selection function
            self.eval_fn = self.uct_select_child
        else:
            raise ValueError(f"Unknown evaluation method: {name_or_fn}")

    def get_possible_moves(self, tile, game: 'Game') -> List[str]:
        """
        Generate all legal moves from the current game state.

        Args:
            graph: The game board graph
            rules_manager: Manager for game rules

        Returns:
            List of possible moves as strings
        """
        possible_moves = []

        # Try to place each available tile on each empty neighbor position
        vertices = game.game_data.graph.get_verticies()
        can_place_meeple = game.get_current_player().get_meeples() > 0
        meeple_indices = (
            range(-1, len(self.meeple_placement_list))
            if can_place_meeple
            else (-1,)
        )

        # Try to place the tile next to each existing vertex
        for vertex_id, vertex in vertices.items():
            # Try each direction (North, South, East, West)
            for direction in ['N', 'S', 'E', 'W']:
                # Check if this side is free
                directions = game.game_data.tiles_info.direction_dict
                if vertex.is_neighbor_free(directions.get(direction, 0)):
                    # Try each rotation (0, 90, 180, 270 degrees)
                    for rotation in range(4):
                        # -1 means no meeple placement
                        for meeple in meeple_indices:
                            if meeple == -1:
                                move = f"{tile}/{vertex_id}{direction}"\
                                    f"{rotation}"
                            else:
                                move = f"{tile}/{vertex_id}{direction}"\
                                    f"{rotation}"\
                                    f"/{self.meeple_placement_list[meeple]}"
                            # Verify the move is legal
                            id_player = game.get_current_player().get_id()
                            if game.game_data.rules_manager.check_move(
                                move,
                                game.game_data.graph,
                                game.river_manager,
                                current_player_id=id_player,
                            ):
                                possible_moves.append(move)
        return possible_moves

    def terminal(self, tiles_info: ITilesInfo) -> bool:
        """Check if the game is in a terminal state (no more moves)."""
        # This is a simplified check -
        # you should implement this based on your game rules

        # If no more tiles are available, the game is terminal
        total_tiles = sum(tiles_info.tiles_count.values())
        if total_tiles == 0:
            return True

        return False

    def uct_select_child(self, node: MCTSNode, c=1.41):
        return max(
            node.get_children(),
            key=lambda child: (
                child.get_total_reward() / child.get_visits
                + c * math.sqrt(math.log(node.get_visits()) /
                                child.get_visits())
            )
        )

    def expand(self, node: MCTSNode):
        move = node.get_untried_moves().pop()
        self.play_move_for_ai(
            node.get_state(), move)

        child = MCTSNode(
            game=node.get_state(),
            mcts_player=self,
            parent=node,
            move=move,
            player=node.get_state().get_current_player(),
        )

        node.get_children().append(child)
        return child

    def rollout(self, state: 'Game'):
        counter = 0
        while not self.terminal(
                state.game_data.tiles_info) and time.time() < self.end_time:
            moves = self.get_possible_moves(
                state.game_data.current_hand, state)
            # Bound dead-hand retries within one rollout step to avoid
            # spinning forever on states with no playable continuation.
            dead_hand_retries = 0
            max_dead_hand_retries = (
                len(state.game_data.deck.tiles)
                + len(state.game_data.deck.river_tiles)
                + 1
            )
            while not moves:
                if time.time() >= self.end_time:
                    return counter
                if dead_hand_retries >= max_dead_hand_retries:
                    return counter
                _discard_unplayable_tile(state, state.game_data.current_hand)
                state.game_data.current_hand = None
                drawn_tile = state.draw_tile()
                if drawn_tile is None:
                    return counter
                dead_hand_retries += 1
                moves = self.get_possible_moves(
                    state.game_data.current_hand, state)

            move = random.choice(moves)
            self.play_move_for_ai(
                state, move)
            counter += 1

        return counter

    def compute_reward(self, state: 'Game', root_player_id):
        scores = {i: state.game_data.players[i].get_score().score
                  for i in range(len(state.game_data.players))}

        vp1 = scores[root_player_id]
        vp2 = max(v for p, v in scores.items() if p != root_player_id)

        return vp1 - vp2

    def backpropagate(self, node: MCTSNode, reward: float, counter: int):
        state: 'Game' = node.get_state()
        while counter > 0:
            self.undo_for_ai(state)
            counter -= 1
        while node.get_parent() is not None:
            node.add_visitor(1)
            node.add_reward(reward)
            node = node.get_parent()
            self.undo_for_ai(state)

    def mcts(self, game_root: 'Game'):
        root = MCTSNode(game_root, self)
        root_player = game_root.get_current_player()

        hand_to_restore: str = game_root.game_data.current_hand

        deck_to_restore: list[str] = game_root.game_data.deck.tiles.copy()
        river_deck_to_restore: list[str] = (
            game_root.game_data.deck.river_tiles.copy()
        )

        river_active_to_restore: bool = game_root.river_manager.river_active
        river_previous_direction_to_restore: int = (
            game_root.river_manager.river_previous_opposite_direction
        )
        river_turn_to_restore: int | None = game_root.river_manager.river_turn

        player_order_to_restore: int = game_root.game_data.current_player_order_list

        score_to_restore: list[int] = [
            game_root.game_data.players[i].score.score
            for i in range(len(game_root.game_data.players))]

        meeples_to_restore = copy.deepcopy(
            game_root.game_data.graph.get_meeples())

        player_meeples_to_restore: list[int] = [
            game_root.game_data.players[i].get_meeples()
            for i in range(len(game_root.game_data.players))]

        # Save land components tracking to prevent ID corruption during
        # simulations
        lands_components_to_restore = copy.deepcopy(
            game_root.game_data.graph.lands_components)
        next_set_id_to_restore = copy.deepcopy(
            game_root.game_data.graph.next_set_id)

        while time.time() < self.end_time:
            node: MCTSNode = root
            state = game_root

            # 🔍 SELECTION
            while node.get_untried_moves() == [] and node.get_children():
                node = self.eval_fn(node)
                self.play_move_for_ai(
                    node.get_state(), node.get_move())

            # 🌱 EXPANSION
            if node.get_untried_moves():
                node = self.expand(node)

            # 🎲 SIMULATION
            counter: int = self.rollout(state)

            # 🧮 REWARD
            reward = self.compute_reward(state, root_player.get_id())

            # 🔁 BACKPROP
            self.backpropagate(node, reward, counter)

            game_root.game_data.current_hand = hand_to_restore

            game_root.game_data.deck.tiles = deck_to_restore.copy()
            game_root.game_data.deck.river_tiles = river_deck_to_restore.copy()

            game_root.game_data.current_player_order_list = player_order_to_restore

            game_root.river_manager.river_active = river_active_to_restore
            game_root.river_manager.river_previous_opposite_direction = (
                river_previous_direction_to_restore
            )
            game_root.river_manager.river_turn = river_turn_to_restore

            for i in range(len(game_root.game_data.players)):
                game_root.game_data.players[i].score.score = score_to_restore[i]
                game_root.game_data.players[i].meeples = player_meeples_to_restore[i]

            game_root.game_data.graph.set_meeples(meeples_to_restore)
            # Restore land components to prevent ID corruption
            game_root.game_data.graph.lands_components = copy.deepcopy(
                lands_components_to_restore)
            game_root.game_data.graph.next_set_id = copy.deepcopy(
                next_set_id_to_restore)

        # 🏁 Choose the best move among expanded children.
        # If time ran out before expansion, fall back to a legal root move.
        if not root.children:
            if root.untried_moves:
                return random.choice(root.untried_moves)
            return ""

        best_child: MCTSNode = max(
            root.children, key=lambda c: c.get_total_reward()
            / float(c.get_visits()))

        game_root.game_data.graph.set_meeples(meeples_to_restore)
        game_root.game_data.deck.tiles = deck_to_restore.copy()
        game_root.game_data.deck.river_tiles = river_deck_to_restore.copy()
        game_root.game_data.current_player_order_list = player_order_to_restore
        game_root.river_manager.river_active = river_active_to_restore
        game_root.river_manager.river_previous_opposite_direction = (
            river_previous_direction_to_restore
        )
        game_root.river_manager.river_turn = river_turn_to_restore
        # Restore land components to prevent ID corruption
        game_root.game_data.graph.lands_components = copy.deepcopy(
            lands_components_to_restore)
        game_root.game_data.graph.next_set_id = copy.deepcopy(
            next_set_id_to_restore)
        for i in range(len(game_root.game_data.players)):
            game_root.game_data.players[i].meeples = player_meeples_to_restore[i]
        game_root.game_data.current_hand = hand_to_restore
        return best_child.get_move()

    def undo_for_ai(self, game: 'Game') -> None:
        """Undo the last AI move."""
        if game.game_data.history.past_moves:
            previous_play = game.game_data.history.pop_past()
            game.game_data.history.push_future(previous_play)
            game.game_data.board.remove_tile_from_board(
                build_str(previous_play),
                game.game_data.graph,
                game.game_data.tiles_info,
                game.game_data.history,
                players=game.game_data.players)
            number_of_players = game.get_number_of_players()
            game.game_data.current_player_order_list = (
                game.game_data.current_player_order_list - 1) % number_of_players
            _restore_drawn_tile_after_undo(
                game,
                previous_play.move_str.split('/')[0],
            )
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
                ) = (
                    self._sim_state_stack.pop()
                )
                for pid, score in saved_scores.items():
                    game.game_data.players[pid].get_score().set_points(score)
                for pid, meeples in saved_meeples.items():
                    game.game_data.players[pid].meeples = meeples
                game.game_data.board.scored_components = saved_scored
                game.game_data.graph.lands_components = saved_lands_components
                game.game_data.graph.next_set_id = saved_next_set_id

    def play_move_for_ai(self, game: 'Game', move: str) -> None:
        """Play move for AI exploring the possibilities."""
        tile_code = game.game_data.extract_tile_code(move)
        if tile_code is not None and tile_code != game.game_data.current_hand:
            print(
                f"Vous devez jouer la tuile en main: {game.game_data.current_hand}")
            return False

        ok = game.game_data.rules_manager.check_move(
            move,
            game.game_data.graph,
            game.river_manager,
            current_player_id=game.get_current_player().get_id(),
        )
        if ok:
            # Snapshot scoring state before modifying it so undo_for_ai can
            # fully restore the real game state.
            saved_scores = {
                pid: p.get_score_int() for pid,
                p in game.game_data.players.items()}
            saved_meeples = {
                pid: p.get_meeples() for pid,
                p in game.game_data.players.items()}
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
                game.get_current_player())
            game.game_data.current_hand = None
            number_of_players = game.get_number_of_players()
            game.game_data.current_player_order_list = (
                game.game_data.current_player_order_list + 1) % number_of_players
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


class AIModelManager:
    """
    Manager for AI model operations in the game.
    """

    def __init__(self, depth: int = 4, eval_name: str = "STAR1"):
        """
        Initialize the AI Model Manager.

        Args:
            depth: Maximum search depth for Expectimax algorithm
        """
        self.player = ExpectimaxPlayer(depth=depth, eval_name=eval_name)

    def choose_best_move(
        self,
        graph: IGraphData,
        tiles_info: ITilesInfo,
        rules_manager: RulesManager,
        ai_score: int,
        opponent_score: int,
    ) -> Optional[str]:
        """
        Choose the best move for the AI using Expectimax pruning.

        Args:
            graph: The game board graph
            tiles_info: Information about available tiles
            rules_manager: Manager for game rules
            ai_score: Current AI player's score
            opponent_score: Opponent's score

        Returns:
            The best move found, or None if no moves available
        """
        self.player.nodes_explored = 0

        _, best_move = self.player.expectimax(
            graph=graph,
            tiles_info=tiles_info,
            rules_manager=rules_manager,
            depth=self.player.depth,
            alpha=float("-inf"),
            beta=float("inf"),
            is_maximizing=True,
            current_player_score=ai_score,
            opponent_score=opponent_score,
        )

        print(f"AI explored {self.player.nodes_explored} nodes")

        return best_move

    def set_search_depth(self, depth: int) -> None:
        """
        Set the search depth for the AI.

        Args:
            depth: Maximum search depth
        """
        self.player.depth = depth

    def set_evaluation_method(self, name_or_fn) -> None:
        """Change the evaluation method used by the AI at runtime."""
        self.player.set_evaluation_method(name_or_fn)


# Global AI manager instance
_ai_manager: Optional[AIModelManager] = None


def initialize_ai(depth: int = 4, eval_name: str = "STAR1") -> None:
    """
    Initialize the global AI manager.

    Args:
        depth: Maximum search depth for Expectimax algorithm
    """
    global _ai_manager
    _ai_manager = AIModelManager(depth=depth, eval_name=eval_name)


def is_ai_player(play: MoveRecord) -> bool:
    """
    Check if a move was made by the AI player.

    Args:
        play: The move record to check

    Returns:
        True if the move was made by AI, False otherwise
    """
    # This would need to be tracked when the move is created
    # For now, returning False - you'll need to mark AI moves in your move
    # record
    return getattr(play, "is_ai_move", False)


def get_ai_move(
    graph: IGraphData,
    tiles_info: ITilesInfo,
    rules_manager: RulesManager,
    ai_score: int,
    opponent_score: int,
) -> Optional[str]:
    """
    Get the best move for the AI player.

    Args:
        graph: The game board graph
        tiles_info: Information about available tiles
        rules_manager: Manager for game rules
        ai_score: Current AI player's score
        opponent_score: Opponent's score

    Returns:
        The best move found, or None if no moves available
    """

    if _ai_manager is None:
        initialize_ai()

    return _ai_manager.choose_best_move(
        graph, tiles_info, rules_manager, ai_score, opponent_score
    )
