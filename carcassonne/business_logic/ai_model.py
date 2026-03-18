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
    from .game import Game
from carcassonne.business_logic.heuristic import evaluate_state as heuristic_evaluate_state

import copy


class RandomPlayer:

    # Example positions for meeple placement
    meeple_placement_list = ['NW', 'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'C']

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
        vertices = game.graph.get_verticies()

        # Try to place the tile next to each existing vertex
        for vertex_id, vertex in vertices.items():
            # Try each direction (North, South, East, West)
            for direction in ['N', 'S', 'E', 'W']:
                # Check if this side is free
                if vertex.is_neighbor_free(game.tiles_info.direction_dict.get(direction, 0)):
                    # Try each rotation (0, 90, 180, 270 degrees)
                    for rotation in range(4):
                        # -1 means no meeple placement
                        for meeple in range(-1, len(self.meeple_placement_list)):
                            if meeple == -1:
                                move = f"{tile}/{vertex_id}{direction}{rotation}"
                            else:
                                move = f"{tile}/{vertex_id}{direction}{rotation}/{self.meeple_placement_list[meeple]}"
                            # Verify the move is legal
                            move_parts = move.split('/')
                            if game.rules_manager.is_correctly_formed_move(move, game.graph):
                                if game.rules_manager.is_legal_move(move_parts, game.graph):
                                    possible_moves.append(move)
        return possible_moves

    def random_move(self, tile, game: 'Game') -> str:
        """Select a random move from the list of possible moves."""
        import random as r

        possible_moves = self.get_possible_moves(tile, game)

        return r.choice(possible_moves) if possible_moves else None


class ExpectimaxPlayer:
    """
    AI player using Expectimax pruning algorithm for intelligent move selection.
    """

    L = -100  # Should be minimum of evaluation function
    U = 100  # Should be maximum of evaluation function

    # Example positions for meeple placement
    meeple_placement_list = ['NW', 'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'C']

    def __init__(self, game: 'Game', start_time: float, max_time: float, depth: int, is_maximizing: bool = True, eval_name: str = "", eval_fn=None):
        """
        Initialize the Expectimax AI player.

        Args:
            depth: Maximum depth for the search tree (default: 4)
            is_maximizing: Whether this player is maximizing (True for AI, False for opponent)
        """
        self.game = game
        self.depth = depth
        self.is_maximizing = is_maximizing
        self.nodes_explored = 0
        # evaluation function (callable(graph, ai_score, opponent_score) -> float)
        if eval_fn is not None:
            self.eval_fn = eval_fn
        else:
            self.set_evaluation_method(eval_name)
        self.depth_max = depth
        self.start_time = start_time
        self.max_time = max_time

    def set_evaluation_method(self, name_or_fn):
        """Set evaluation by name or by callable.

        Accepts a callable(graph, ai_score, opponent_score) or a string name.
        """
        if callable(name_or_fn):
            self.eval_fn = name_or_fn
            return

        name = (name_or_fn or '').upper()
        if name == '':
            self.eval_fn = heuristic_evaluate_state
        else:
            raise ValueError(f"Unknown evaluation method: {name_or_fn}")

    def get_possible_moves(self, tile: str, game: 'Game') -> List[str]:
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
        vertices = copy.deepcopy(game.graph.get_verticies())

        # Try to place the tile next to each existing vertex
        for vertex_id, vertex in vertices.items():
            # Try each direction (North, South, East, West)
            for direction in ['N', 'S', 'E', 'W']:
                # Check if this side is free
                if vertex.is_neighbor_free(game.tiles_info.direction_dict.get(direction, 0)):
                    # Try each rotation (0, 90, 180, 270 degrees)
                    for rotation in range(4):
                        # -1 means no meeple placement
                        for meeple in range(-1, len(self.meeple_placement_list)):
                            if meeple == -1:
                                move = f"{tile}/{vertex_id}{direction}{rotation}"
                            else:
                                move = f"{tile}/{vertex_id}{direction}{rotation}/{self.meeple_placement_list[meeple]}"
                            # Verify the move is legal
                            if game.rules_manager.check_move(move, game.graph):
                                possible_moves.append(move)

        return possible_moves

    def search(self, game: 'Game', depth: int, alpha: float, beta: float, player_to_max: int, next_player: int) -> Tuple[float, str]:
        """Recursive search function for Expectimax algorithm. Adapt between Max and Min nodes based on the player parameter."""
        if self.terminal(game.tiles_info) or depth == 0 or time.time() - self.start_time > self.max_time:
            return self.eval_fn(game, player_to_max, next_player), ''
        restored_hand = game.current_hand
        best_move = ''
        if player_to_max == next_player:  # Max node
            max_eval = float('-inf')
            possible_moves = self.get_possible_moves(game.current_hand, game)
            for move in possible_moves:
                res = self.play_move_for_ai(game, move)
                if (not res):
                    print("SEARCH MAX DIDNT WORK")
                    continue
                eval_score = self.star25(
                    game, depth - 1, alpha, beta, player_to_max, (next_player + 1) % len(game.players))

                self.undo_for_ai(game)
                # print("Move undone")
                # game.get_board()
                game.current_hand = restored_hand
                if eval_score > max_eval and depth == self.depth_max:
                    best_move = move
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha or time.time() - self.start_time > self.max_time:
                    break
            return max_eval, best_move
        else:  # Min node (opponent's turn)
            min_eval = float('inf')
            possible_moves = self.get_possible_moves(game.current_hand, game)
            for move in possible_moves:
                res = self.play_move_for_ai(game, move)
                if (not res):
                    print("SEARCH MIN DIDNT WORK")
                    game.get_board()
                    print(move)
                    continue
                eval_score = self.star25(
                    game, depth - 1, alpha, beta, player_to_max, (next_player + 1) % len(game.players))

                self.undo_for_ai(game)
                # print("Move undone")
                game.current_hand = restored_hand
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha or time.time() - self.start_time > self.max_time:
                    break
            return min_eval, ''

    def event_prob(self, graph: IGraphData, tile: str, N: dict) -> float:
        """Calculate the probability of a chance event (e.g., drawing a specific tile)."""
        total_tiles_left = sum(N.values())
        if total_tiles_left == 0:
            return 0.0
        return N.get(tile) / total_tiles_left

    def n_probe(self, game: 'Game', alpha: float, beta: float,
                depth: int, player_to_max: int, next_player: int,
                probingFactor: int = 1) -> float:

        moves = self.get_possible_moves(game.current_hand, game)
        # ordonner les moves selon un heuristique rapide à calculer
        # moves = sorted(moves, key=lambda m: self.quick_eval_move(game, m, player_to_max), reverse=True)

        best = alpha

        restored_hand = game.current_hand

        for i in range(min(probingFactor, len(moves))):
            move = moves[i]

            self.play_move_for_ai(game, move)

            value = self.star25(game, depth - 1, best, beta,
                                player_to_max, (next_player + 1) % len(game.players))

            self.undo_for_ai(game)
            game.current_hand = restored_hand

            if value >= beta:
                return beta

            if value > best:
                best = value

        return best

    def apply_chance_event(self, game: 'Game', tile: str) -> None:
        """Apply a chance event (e.g., drawing a tile) to the game state."""
        # TODO: Make the next tile to draw the tile parameter
        game.current_hand = tile
        # TODO: bug happens when we have a river tile (because we can have a river tile while river tiles are commented in deck)
        # game.deck.tiles.remove(tile)

    def num_successors(self, tiles_info: ITilesInfo) -> int:
        """Return the number of possible chance events (e.g., tile draws) from this state."""
        N = {}
        for tile, tile_nb in tiles_info.tiles_count.items():
            if tile_nb > 0:
                N[tile] = tile_nb
        return N

    def terminal(self, tiles_info: ITilesInfo) -> bool:
        """Check if the game is in a terminal state (no more moves)."""
        # This is a simplified check - you should implement this based on your game rules

        # If no more tiles are available, the game is terminal
        total_tiles = sum(tiles_info.tiles_count.values())
        if total_tiles == 0:
            return True

        return False

    def star25(self, game: 'Game', depth: int,
               alpha: float, beta: float,
               player_to_max: int, next_player: int) -> float:

        if self.terminal(game.tiles_info) or depth == 0 or time.time() - self.start_time > self.max_time:
            return self.eval_fn(game, player_to_max, next_player)

        successors = self.num_successors(game.tiles_info)

        total_tiles = sum(successors.values())

        # probabilités
        probs = {tile: count / total_tiles for tile,
                 count in successors.items()}
        probs = dict(sorted(probs.items(), key=lambda x: -x[1]))

        cur_x = 0
        cur_y = 1
        w = {}

        '''
        # ---------- PROBING PHASE ----------
        for tile, prob in probs.items():

            cur_y -= prob

            cur_beta = (beta - self.L * cur_y - cur_x) / prob

            self.applyChanceEvent(game, tile)

            value = self.nProbe(
                game,
                alpha,
                cur_beta,
                depth - 1,
                player_to_max,
                next_player
            )

            w[tile] = value

            if value >= cur_beta:
                return beta

            cur_x += prob * value
        '''

        # ---------- SEARCH PHASE ----------
        cur_x = 0
        cur_y = 1

        for tile, prob in probs.items():

            cur_y -= prob

            cur_alpha = (alpha - cur_x - self.U * cur_y) / prob
            cur_beta = (beta - cur_x - self.L * cur_y) / prob

            ax = max(self.L, cur_alpha)
            bx = min(self.U, cur_beta)

            self.apply_chance_event(game, tile)

            value, _ = self.search(
                game,
                depth - 1,
                ax,
                bx,
                player_to_max,
                next_player
            )

            if value >= cur_beta:
                return beta

            if value <= cur_alpha:
                return alpha

            if time.time() - self.start_time > self.max_time:
                break

            cur_x += prob * value

        return cur_x

    def undo_for_ai(self, game: 'Game') -> None:
        """Undo the last AI move."""
        if game.history.past_moves:
            previous_play = game.history.pop_past()
            game.history.push_future(previous_play)
            game.board.remove_tile_from_board(build_str(
                previous_play), game.graph, game.tiles_info, game.history, players=game.players)
            game.current_player_order_list = (
                game.current_player_order_list - 1) % game.get_number_of_players()
            game.deck.tiles.append(previous_play.move_str.split('/')[0])
            # print(game.graph.get_verticies())

    def play_move_for_ai(self, game: 'Game', move: str) -> None:
        """Play move for AI exploring the possibilities."""
        tile_code = game.extract_tile_code(move)
        if tile_code is not None and tile_code != game.current_hand:
            print(f"Vous devez jouer la tuile en main: {game.current_hand}")
            return False

        ok = game.rules_manager.check_move(move, game.graph)
        if ok:
            game.board.add_tile_to_board(move, game.graph, game.tiles_info, game.history,
                                         game.players, game.players_order, game.get_current_player())
            game.current_hand = None
            game.current_player_order_list = (
                game.current_player_order_list + 1) % game.get_number_of_players()
        # game.get_board()
        # print("----------------------------------------------------")
            return True
        # print("THINGD WENT WRONG")
        return False


class MCTSNode:
    def __init__(self, game: 'Game', parent=None, move=None, player=None):
        self.state = game
        self.parent = parent
        self.move = move  # coup qui mène à ce noeud
        self.player = player  # joueur qui a joué ce coup

        self.children = []
        self.untried_moves = MCTSPlayer.get_possible_moves(
            game.current_hand, game)

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

    def __init__(self, game: 'Game', start_time: float, max_time: float, eval_name: str = "", eval_fn=None):
        """
        Initialize the Expectimax AI player.

        Args:
            depth: Maximum depth for the search tree (default: 4)
            is_maximizing: Whether this player is maximizing (True for AI, False for opponent)
        """
        self.game = game
        self.nodes_explored = 0
        # evaluation function (callable(graph, ai_score, opponent_score) -> float)
        if eval_fn is not None:
            self.eval_fn = eval_fn
        else:
            self.set_evaluation_method(eval_name)
        self.start_time = start_time
        self.max_time = max_time

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
        vertices = game.graph.get_verticies()

        # Try to place the tile next to each existing vertex
        for vertex_id, vertex in vertices.items():
            # Try each direction (North, South, East, West)
            for direction in ['N', 'S', 'E', 'W']:
                # Check if this side is free
                if vertex.is_neighbor_free(game.tiles_info.direction_dict.get(direction, 0)):
                    # Try each rotation (0, 90, 180, 270 degrees)
                    for rotation in range(4):
                        # -1 means no meeple placement
                        for meeple in range(-1, len(self.meeple_placement_list)):
                            if meeple == -1:
                                move = f"{tile}/{vertex_id}{direction}{rotation}"
                            else:
                                move = f"{tile}/{vertex_id}{direction}{rotation}/{self.meeple_placement_list[meeple]}"
                            # Verify the move is legal
                            move_parts = move.split('/')
                            if game.rules_manager.is_correctly_formed_move(move, game.graph):
                                if game.rules_manager.is_legal_move(move_parts, game.graph):
                                    possible_moves.append(move)
        return possible_moves

    def terminal(self, tiles_info: ITilesInfo) -> bool:
        """Check if the game is in a terminal state (no more moves)."""
        # This is a simplified check - you should implement this based on your game rules

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
            node.get_state(), node.get_move())

        child = MCTSNode(
            state=node.get_state(),
            parent=node,
            move=move,
            player=node.get_state().get_current_player(),
        )

        node.get_children().append(child)
        return child

    def rollout(self, state: 'Game'):
        counter = 0
        while not self.terminal(state.tiles_info):
            moves = self.get_possible_moves(state.current_hand, state)
            move = random.choice(moves)
            state = self.play_move_for_ai(
                state, move)
            counter += 1

        return counter

    def compute_reward(self, state: 'Game', root_player):
        scores = state.get_scores()

        vp1 = scores[root_player]
        vp2 = max(v for p, v in scores.items() if p != root_player)

        return vp1 - vp2

    def backpropagate(self, node: MCTSNode, reward: float, counter: int):
        state: 'Game' = node.get_state()
        while counter > 0:
            self.undo_for_ai(state)
            counter -= 1
        while node is not None:
            node.add_visitor(1)
            node.add_reward(reward)
            node = node.get_parent()
            self.undo_for_ai(state)

    def mcts(self, game_root: 'Game'):
        root = MCTSNode(game_root)
        root_player = game_root.get_current_player()

        end_time = time.time() + self.max_time

        while time.time() < end_time:
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
            reward = self.compute_reward(state, root_player)

            # 🔁 BACKPROP
            self.backpropagate(node, reward, counter)

        # 🏁 Choisir le meilleur coup
        best_child: MCTSNode = max(
            root.children, key=lambda c: c.get_total_reward() / float(c.get_visits()))
        return best_child.get_move()

    def undo_for_ai(self, game: 'Game') -> None:
        """Undo the last AI move."""
        if game.history.past_moves:
            previous_play = game.history.pop_past()
            game.history.push_future(previous_play)
            game.board.remove_tile_from_board(build_str(
                previous_play), game.graph, game.tiles_info, game.history, players=game.players)
            game.current_player_order_list = (
                game.current_player_order_list - 1) % game.get_number_of_players()
            game.deck.tiles.append(previous_play.move_str.split('/')[0])
            # print(game.graph.get_verticies())

    def play_move_for_ai(self, game: 'Game', move: str) -> None:
        """Play move for AI exploring the possibilities."""
        tile_code = game.extract_tile_code(move)
        if tile_code is not None and tile_code != game.current_hand:
            print(f"Vous devez jouer la tuile en main: {game.current_hand}")
            return False

        ok = game.rules_manager.check_move(move, game.graph)
        if ok:
            game.board.add_tile_to_board(move, game.graph, game.tiles_info, game.history,
                                         game.players, game.players_order, game.get_current_player())
            game.current_hand = None
            game.current_player_order_list = (
                game.current_player_order_list + 1) % game.get_number_of_players()
        # game.get_board()
        # print("----------------------------------------------------")
            return True
        # print("THINGD WENT WRONG")
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

    def choose_best_move(self, graph: IGraphData, tiles_info: ITilesInfo,
                         rules_manager: RulesManager, ai_score: int,
                         opponent_score: int) -> Optional[str]:
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
            alpha=float('-inf'),
            beta=float('inf'),
            is_maximizing=True,
            current_player_score=ai_score,
            opponent_score=opponent_score
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
    # For now, returning False - you'll need to mark AI moves in your move record
    return getattr(play, 'is_ai_move', False)


def get_ai_move(graph: IGraphData, tiles_info: ITilesInfo,
                rules_manager: RulesManager, ai_score: int,
                opponent_score: int) -> Optional[str]:
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
    global _ai_manager

    if _ai_manager is None:
        initialize_ai()

    return _ai_manager.choose_best_move(graph, tiles_info, rules_manager, ai_score, opponent_score)
