"""MCTS AI player (Monte Carlo Tree Search)."""

from __future__ import annotations

import copy
import math
import os
import random
import time
from pathlib import Path
from typing import List, TYPE_CHECKING

from carcassonne.interfaces.i_tiles_info import ITilesInfo
from carcassonne.business_logic.move_serializer import build_str
from carcassonne.i18n import gettext as _
from carcassonne.business_logic.ai._utils import (
    _discard_unplayable_tile,
    _restore_drawn_tile_after_undo,
)

if TYPE_CHECKING:
    from carcassonne.business_logic.game.game import Game

DEFAULT_MCTS_ML_DIR = Path(__file__).resolve().parents[2] / "datas" / "mcts_ml"
DEFAULT_MCTS_ML_MODEL_PATH = str(DEFAULT_MCTS_ML_DIR / "mcts_selection.keras")


class MCTSNode:
    def __init__(
        self,
        game: "Game",
        mcts_player: "MCTSPlayer",
        parent=None,
        move=None,
        player=None,
    ):
        self.state = game
        self.parent = parent
        self.move = move  # move leading to this node
        self.player = player  # player who played this move
        self.mcts_player = mcts_player

        self.children = []
        self.untried_moves = mcts_player.get_possible_moves(
            game.game_data.current_hand, game
        )

        self.visits = 0
        self.total_reward = 0.0  # sum of rewards

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
    meeple_placement_list = ["NW", "N", "NE", "E", "SE", "S", "SW", "W", "C"]

    def __init__(
        self,
        game: "Game",
        start_time: float,
        max_time: float,
        eval_name: str = "",
        eval_fn=None,
    ):
        """
        Initialize the MCTS AI player.

        Args:
            game: The current game state
            start_time: Timestamp when the search started
            max_time: Maximum time budget in seconds
            eval_name: Name of the selection method ("UCT" or "ML")
            eval_fn: Optional callable overriding the selection method
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
        self.ml_model = None
        self._ml_model_attempted = False

    def set_evaluation_method(self, name_or_fn):
        """Set evaluation by name or by callable.

        Accepts a callable(graph, ai_score, opponent_score) or a string name.
        """
        if callable(name_or_fn):
            self.eval_fn = name_or_fn
            return

        name = (name_or_fn or "").upper()
        if name in ("", "UCT"):
            # default selection function
            self.eval_fn = self.uct_select_child
        elif name == "ML":
            self.eval_fn = self.ml_select_child
        else:
            raise ValueError(f"Unknown evaluation method: {name_or_fn}")

    def _load_ml_model(self) -> bool:
        """Load Keras model used by ML selection, if available."""
        if self.ml_model is not None:
            return True
        if self._ml_model_attempted:
            return False

        self._ml_model_attempted = True
        model_path = os.environ.get(
            "CARCASSONNE_MCTS_MODEL_PATH", DEFAULT_MCTS_ML_MODEL_PATH
        )

        try:
            from keras.models import load_model
        except Exception:
            return False

        if not os.path.exists(model_path):
            return False

        try:
            self.ml_model = load_model(model_path)
        except Exception:
            self.ml_model = None
            return False

        return True

    def _extract_ml_features(
        self, node: MCTSNode, child: MCTSNode
    ) -> list[float]:
        """Build a compact numerical feature vector for a child node."""
        child_visits = max(child.get_visits(), 1)
        node_visits = max(node.get_visits(), 1)
        avg_reward = child.get_total_reward() / float(child_visits)
        exploration = math.sqrt(
            math.log(node_visits + 1.0) / float(child_visits)
        )

        current_player = child.get_state().get_current_player()
        has_meeple_in_move = 1.0 if child.get_move().count("/") >= 2 else 0.0

        return [
            avg_reward,
            float(child.get_total_reward()),
            float(child_visits),
            float(node_visits),
            float(len(child.get_children())),
            float(len(child.get_untried_moves())),
            float(current_player.get_meeples()),
            float(current_player.get_score_int()),
            has_meeple_in_move,
            exploration,
        ]

    def ml_select_child(self, node: MCTSNode, c=1.41):
        """Select child using a trained Keras model (fallback to UCT)."""
        if not node.get_children():
            raise ValueError("Cannot select a child from a leaf node")

        if not self._load_ml_model():
            return self.uct_select_child(node, c)

        features = [
            self._extract_ml_features(node, child)
            for child in node.get_children()
        ]

        try:
            predictions = self.ml_model.predict(features, verbose=0)
        except Exception:
            return self.uct_select_child(node, c)

        scored_children: list[tuple[float, MCTSNode]] = []
        for idx, child in enumerate(node.get_children()):
            pred = predictions[idx]
            if isinstance(pred, (list, tuple)):
                pred_score = float(pred[0]) if pred else 0.0
            else:
                try:
                    pred_score = float(pred)
                except TypeError:
                    pred_score = float(pred.item())

            # Keep small UCT tie-break to avoid deterministic deadlocks.
            child_visits = max(child.get_visits(), 1)
            node_visits = max(node.get_visits(), 1)
            uct_tiebreak = c * math.sqrt(
                math.log(node_visits + 1.0) / float(child_visits)
            )
            scored_children.append((pred_score + 1e-6 * uct_tiebreak, child))

        return max(scored_children, key=lambda pair: pair[0])[1]

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
        vertices = game.game_data.graph.get_vertices()
        can_place_meeple = game.get_current_player().get_meeples() > 0
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
                directions = game.game_data.tiles_info.direction_dict
                if vertex.is_neighbor_free(directions.get(direction, 0)):
                    # Try each rotation (0, 90, 180, 270 degrees)
                    for rotation in range(4):
                        # -1 means no meeple placement
                        for meeple in meeple_indices:
                            if meeple == -1:
                                move = (
                                    f"{tile}/{vertex_id}{direction}"
                                    f"{rotation}"
                                )
                            else:
                                move = (
                                    f"{tile}/{vertex_id}{direction}"
                                    f"{rotation}"
                                    f"/{self.meeple_placement_list[meeple]}"
                                )
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
        def uct_score(child: MCTSNode) -> float:
            child_visits = child.get_visits()
            if child_visits <= 0:
                # Always explore unvisited children first.
                return float("inf")

            parent_visits = max(node.get_visits(), 1)
            exploitation = child.get_total_reward() / float(child_visits)
            exploration = c * math.sqrt(
                math.log(parent_visits) / float(child_visits)
            )
            return exploitation + exploration

        return max(node.get_children(), key=uct_score)

    def expand(self, node: MCTSNode):
        move = node.get_untried_moves().pop()
        self.play_move_for_ai(node.get_state(), move)

        child = MCTSNode(
            game=node.get_state(),
            mcts_player=self,
            parent=node,
            move=move,
            player=node.get_state().get_current_player(),
        )

        node.get_children().append(child)
        return child

    def rollout(self, state: "Game"):
        counter = 0
        while (
            not self.terminal(state.game_data.tiles_info)
            and time.time() < self.end_time
        ):
            moves = self.get_possible_moves(
                state.game_data.current_hand, state
            )
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
                # Use DeckManager directly when available to avoid triggering
                # real end-game side effects through Game.draw_tile().
                if hasattr(state, "deck_manager"):
                    drawn_tile = state.deck_manager.draw_tile(silent=True)
                else:
                    drawn_tile = state.draw_tile(silent=True)
                if drawn_tile is None:
                    return counter
                dead_hand_retries += 1
                moves = self.get_possible_moves(
                    state.game_data.current_hand, state
                )

            move = random.choice(moves)
            self.play_move_for_ai(state, move)
            counter += 1

        return counter

    def compute_reward(self, state: "Game", root_player_id):
        scores = {
            i: state.game_data.players[i].get_score().score
            for i in range(len(state.game_data.players))
        }

        vp1 = scores[root_player_id]
        vp2 = max(v for p, v in scores.items() if p != root_player_id)

        return vp1 - vp2

    def backpropagate(self, node: MCTSNode, reward: float, counter: int):
        state: "Game" = node.get_state()
        while counter > 0:
            self.undo_for_ai(state)
            counter -= 1
        while node is not None:
            node.add_visitor(1)
            node.add_reward(reward)
            parent = node.get_parent()
            if parent is not None:
                self.undo_for_ai(state)
            node = parent

    def mcts(self, game_root: "Game"):
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

        player_order_to_restore: int = (
            game_root.game_data.current_player_order_list
        )
        no_playable_tiles_to_restore = getattr(
            game_root.game_data,
            "no_playable_tiles_remaining",
            None,
        )
        end_game_scored_to_restore = getattr(
            game_root.game_data,
            "_end_game_scored",
            None,
        )

        score_to_restore: list[int] = [
            game_root.game_data.players[i].score.score
            for i in range(len(game_root.game_data.players))
        ]

        meeples_to_restore = copy.deepcopy(
            game_root.game_data.graph.get_meeples()
        )

        player_meeples_to_restore: list[int] = [
            game_root.game_data.players[i].get_meeples()
            for i in range(len(game_root.game_data.players))
        ]

        # Save land components tracking to prevent ID corruption during
        # simulations
        lands_components_to_restore = copy.deepcopy(
            game_root.game_data.graph.lands_components
        )
        next_set_id_to_restore = copy.deepcopy(
            game_root.game_data.graph.next_set_id
        )

        while time.time() < self.end_time:
            node: MCTSNode = root
            state = game_root

            # SELECTION
            while node.get_untried_moves() == [] and node.get_children():
                node = self.eval_fn(node)
                self.play_move_for_ai(node.get_state(), node.get_move())

            # EXPANSION
            if node.get_untried_moves():
                node = self.expand(node)

            # SIMULATION
            counter: int = self.rollout(state)

            # REWARD
            reward = self.compute_reward(state, root_player.get_id())

            # BACKPROP
            self.backpropagate(node, reward, counter)

            game_root.game_data.current_hand = hand_to_restore

            game_root.game_data.deck.tiles = deck_to_restore.copy()
            game_root.game_data.deck.river_tiles = (
                river_deck_to_restore.copy()
            )

            game_root.game_data.current_player_order_list = (
                player_order_to_restore
            )
            if no_playable_tiles_to_restore is not None:
                game_root.game_data.no_playable_tiles_remaining = (
                    no_playable_tiles_to_restore
                )
            if end_game_scored_to_restore is not None:
                game_root.game_data._end_game_scored = (
                    end_game_scored_to_restore
                )

            game_root.river_manager.river_active = river_active_to_restore
            game_root.river_manager.river_previous_opposite_direction = (
                river_previous_direction_to_restore
            )
            game_root.river_manager.river_turn = river_turn_to_restore

            for i in range(len(game_root.game_data.players)):
                game_root.game_data.players[i].score.score = (
                    score_to_restore[i]
                )
                game_root.game_data.players[i].meeples = (
                    player_meeples_to_restore[i]
                )

            game_root.game_data.graph.set_meeples(meeples_to_restore)
            # Restore land components to prevent ID corruption
            game_root.game_data.graph.lands_components = copy.deepcopy(
                lands_components_to_restore
            )
            game_root.game_data.graph.next_set_id = copy.deepcopy(
                next_set_id_to_restore
            )

        # Choose the best move among expanded children.
        # If time ran out before expansion, fall back to a legal root move.
        if not root.children:
            if root.untried_moves:
                return random.choice(root.untried_moves)
            return ""

        best_child: MCTSNode = max(
            root.children,
            key=lambda c: c.get_total_reward() / float(c.get_visits()),
        )

        game_root.game_data.graph.set_meeples(meeples_to_restore)
        game_root.game_data.deck.tiles = deck_to_restore.copy()
        game_root.game_data.deck.river_tiles = river_deck_to_restore.copy()
        game_root.game_data.current_player_order_list = player_order_to_restore
        if no_playable_tiles_to_restore is not None:
            game_root.game_data.no_playable_tiles_remaining = (
                no_playable_tiles_to_restore
            )
        if end_game_scored_to_restore is not None:
            game_root.game_data._end_game_scored = end_game_scored_to_restore
        game_root.river_manager.river_active = river_active_to_restore
        game_root.river_manager.river_previous_opposite_direction = (
            river_previous_direction_to_restore
        )
        game_root.river_manager.river_turn = river_turn_to_restore
        # Restore land components to prevent ID corruption
        game_root.game_data.graph.lands_components = copy.deepcopy(
            lands_components_to_restore
        )
        game_root.game_data.graph.next_set_id = copy.deepcopy(
            next_set_id_to_restore
        )
        for i in range(len(game_root.game_data.players)):
            game_root.game_data.players[i].meeples = (
                player_meeples_to_restore[i]
            )
        game_root.game_data.current_hand = hand_to_restore
        return best_child.get_move()

    def undo_for_ai(self, game: "Game") -> None:
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
            number_of_players = game.get_number_of_players()
            game.game_data.current_player_order_list = (
                game.game_data.current_player_order_list - 1
            ) % number_of_players
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
                    saved_board_meeples,
                    saved_lands_components,
                    saved_next_set_id,
                ) = self._sim_state_stack.pop()
                for pid, score in saved_scores.items():
                    game.game_data.players[pid].get_score().set_points(score)
                for pid, meeples in saved_meeples.items():
                    game.game_data.players[pid].meeples = meeples
                game.game_data.board.scored_components = saved_scored
                game.game_data.graph.set_meeples(saved_board_meeples)
                game.game_data.graph.lands_components = saved_lands_components
                game.game_data.graph.next_set_id = saved_next_set_id

    def play_move_for_ai(self, game: "Game", move: str) -> None:
        """Play move for AI exploring the possibilities."""
        tile_code = game.game_data.extract_tile_code(move)
        if tile_code is not None and tile_code != game.game_data.current_hand:
            hand = game.game_data.current_hand
            print(_("You must play the tile in hand: {hand}").format(
                hand=hand
            ))
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
                pid: p.get_score_int()
                for pid, p in game.game_data.players.items()
            }
            saved_meeples = {
                pid: p.get_meeples()
                for pid, p in game.game_data.players.items()
            }
            saved_scored = set(game.game_data.board.scored_components)
            saved_board_meeples = copy.deepcopy(
                game.game_data.graph.get_meeples()
            )
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
                game.get_current_player(),
            )
            game.game_data.current_hand = None
            number_of_players = game.get_number_of_players()
            game.game_data.current_player_order_list = (
                game.game_data.current_player_order_list + 1
            ) % number_of_players
            self._sim_state_stack.append(
                (
                    saved_scores,
                    saved_meeples,
                    saved_scored,
                    saved_board_meeples,
                    saved_lands_components,
                    saved_next_set_id,
                )
            )
            return True
        return False
