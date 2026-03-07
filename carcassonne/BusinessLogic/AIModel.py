"""
This module implements the AI player using the Expectimax pruning algorithm.
It provides intelligent move selection for the AI player in Carcassonne.
"""
from typing import List, Tuple, Optional

from carcassonne.Datas.History import MoveRecord
from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData
from carcassonne.BusinessLogic.Interfaces.ITilesInfo import ITilesInfo
from carcassonne.BusinessLogic.RulesManager import RulesManager
from carcassonne.BusinessLogic.Game import Game


def star1(graph: IGraphData, ai_score: int, opponent_score: int) -> float:
    pass


def star2(graph: IGraphData, ai_score: int, opponent_score: int) -> float:
    pass


def star2_5(graph: IGraphData, ai_score: int, opponent_score: int) -> float:
    pass


class RandomPlayer:

    # Example positions for meeple placement
    meeple_placement_list = ['NW', 'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'C']

    def get_possible_moves(self, tile, game: Game) -> List[str]:
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

    def random_move(self, tile, game: Game) -> str:
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

    def __init__(self, game: Game, depth: int = 4, is_maximizing: bool = True, eval_name: str = "STAR1", eval_fn=None):
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
        self.eval_fn = None
        if eval_fn is not None:
            self.eval_fn = eval_fn
        else:
            self.set_evaluation_method(eval_name)

    def set_evaluation_method(self, name_or_fn) -> None:
        """Set evaluation by name ('STAR1','STAR2','STAR2_5') or by callable.

        Accepts a callable(graph, ai_score, opponent_score) or a string name.
        """
        if callable(name_or_fn):
            self.eval_fn = name_or_fn
            return

        name = (name_or_fn or '').upper()
        if name == 'STAR1':
            self.eval_fn = star1
        elif name == 'STAR2':
            self.eval_fn = star2
        elif name in ('STAR2_5', 'STAR2.5', 'STAR25'):
            self.eval_fn = star2_5
        else:
            raise ValueError(f"Unknown evaluation method: {name_or_fn}")

    def get_possible_moves(self, tile: str, game: Game) -> List[str]:
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

    def evaluate_state(self, graph: IGraphData, current_player_score: int,
                       opponent_score: int) -> float:
        """
        Evaluate the current game state for the AI player.
        This is a heuristic function that estimates the value of a position.

        Args:
            graph: The game board graph
            current_player_score: Current player's score
            opponent_score: Opponent's score

        Returns:
            Evaluation score (higher is better for AI)
        """
        if self.eval_fn is None:
            # fallback to simple heuristic if none selected
            score_diff = current_player_score - opponent_score
            board_control = len(graph.get_verticies()) * 5
            incomplete_features_bonus = self._estimate_potential(graph)
            return score_diff + board_control + incomplete_features_bonus

        return self.eval_fn(graph, current_player_score, opponent_score)

    def _estimate_potential(self, graph: IGraphData) -> float:
        """
        Estimate the potential future points from incomplete features.

        Args:
            graph: The game board graph

        Returns:
            Estimated potential points
        """
        # This is a simplified heuristic - you can expand this based on your game rules
        vertices = graph.get_verticies()
        potential = 0

        # Count edges (potential for roads, cities, etc.)
        for vertex in vertices.values():
            # Estimate potential points based on vertex type and completeness
            potential += 10  # Base potential per tile

        return potential

    def search(self, game: Game, depth: int, alpha: float, beta: float, player_to_max: int, next_player: int) -> float:
        """Recursive search function for Expectimax algorithm. Adapt between Max and Min nodes based on the player parameter."""
        if self.terminal(game.tiles_info, game.graph) or depth == 0:
            return self.evaluate_state(game.graph, 0, 0)
        if player_to_max == next_player:  # Max node
            max_eval = float('-inf')
            possible_moves = self.get_possible_moves(game.current_hand, game)
            for move in possible_moves:
                new_game = self.apply_move(game.graph, move)
                eval_score = self.Star25(
                    new_game, depth - 1, alpha, beta, player_to_max, (next_player + 1) % self.nb_players)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:  # Min node (opponent's turn)
            min_eval = float('inf')
            possible_moves = self.get_possible_moves(game.current_hand, game)
            for move in possible_moves:
                new_game = self.apply_move(game.graph, move)
                eval_score = self.Star25(
                    new_game, depth - 1, alpha, beta, player_to_max, (next_player + 1) % self.nb_players)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    def event_probability(self, graph: IGraphData, tile: str, N: dict) -> float:
        """Calculate the probability of a chance event (e.g., drawing a specific tile)."""
        total_tiles_left = sum(N.values())
        if total_tiles_left == 0:
            return 0.0
        return N.get(tile) / total_tiles_left

    def nProbe(self, game: Game, alpha: float, beta: float,
               depth: int, player_to_max: int, next_player: int,
               probingFactor: int = 5):

        moves = self.get_possible_moves(game.current_hand, game)

        best = alpha

        for i in range(min(probingFactor, len(moves))):
            move = moves[i]

            new_graph = self.apply_move(game.graph, move)
            new_game = game.copy()
            new_game.graph = new_graph

            value = self.search(
                new_game,
                depth - 1,
                best,
                beta,
                player_to_max,
                (next_player + 1) % self.nb_players,
            )

            if value >= beta:
                return beta

            if value > best:
                best = value

        return best

    def applyChanceEvent(self, tile: str) -> IGraphData:
        """Apply a chance event (e.g., drawing a tile) to the game state and return the new state."""
        game_copy = self.game.copy()

        # TODO: Make the next tile to draw the tile parameter
        game_copy.current_hand = tile

        return game_copy

    def numSuccesors(self, tiles_info: ITilesInfo) -> int:
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

    def Star25(self, game: Game, depth: int,
               alpha: float, beta: float,
               player_to_max: int, next_player: int):

        if self.terminal(game.tiles_info) or depth == 0:
            return self.evaluate_state(game.graph, 0, 0)

        successors = self.numSuccesors(game.tiles_info)

        total_tiles = sum(successors.values())

        # probabilités
        probs = {tile: count / total_tiles for tile,
                 count in successors.items()}
        probs = dict(sorted(probs.items(), key=lambda x: -x[1]))

        cur_x = 0
        cur_y = 1
        w = {}

        # ---------- PROBING PHASE ----------
        for tile, prob in probs.items():

            cur_y -= prob

            cur_beta = (beta - self.L * cur_y - cur_x) / prob

            succ_game = self.applyChanceEvent(tile)

            value = self.nProbe(
                succ_game,
                tile,
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

        # ---------- SEARCH PHASE ----------
        cur_x = 0
        cur_y = 1

        for tile, prob in probs.items():

            cur_y -= prob

            cur_alpha = (alpha - cur_x - self.U * cur_y) / prob
            cur_beta = (beta - cur_x - self.L * cur_y) / prob

            ax = max(self.L, cur_alpha)
            bx = min(self.U, cur_beta)

            succ_game = self.applyChanceEvent(tile)

            value = self.search(
                succ_game,
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

            cur_x += prob * value

        return cur_x

    def Expectimax(self, current_hand, tiles_info, graph: IGraphData, depth: int, player: int):
        if self.terminal(tiles_info, graph) or depth == 0:
            return self.evaluate_state(graph, 0, 0)
        N = self.numSuccesors(tiles_info, graph)
        sum = 0
        for tile, _ in N.items():
            # Make a copy of the game state and apply the chance event (playing the tile)
            succ = self.applyChanceEvent(tile)
            sum += self.eventProb(graph, tile, N) * self.search(succ, tiles_info,
                                                                graph, depth - 1, player, (player + 1) % nb_players, current_hand)
        return sum

    def expectimax(self, graph: IGraphData, tiles_info: ITilesInfo,
                   rules_manager: RulesManager, depth: int, alpha: float,
                   beta: float, is_maximizing: bool,
                   current_player_score: int, opponent_score: int) -> Tuple[float, Optional[str]]:
        """
        Expectimax algorithm for game tree search.

        Args:
            graph: The game board graph
            tiles_info: Information about available tiles
            rules_manager: Manager for game rules
            depth: Current depth in the search tree
            alpha: Best value for maximizing player
            beta: Best value for minimizing player
            is_maximizing: True if this is a maximizing node
            current_player_score: Current player's score
            opponent_score: Opponent's score

        Returns:
            Tuple of (evaluation_score, best_move)
        """
        self.nodes_explored += 1

        # Terminal node: return evaluation
        if depth == 0:
            eval_score = self.evaluate_state(
                graph, current_player_score, opponent_score)
            return eval_score, None

        # Get all possible moves
        possible_moves = self.get_possible_moves(
            graph, tiles_info, rules_manager)

        # Leaf node: no moves available
        if not possible_moves:
            eval_score = self.evaluate_state(
                graph, current_player_score, opponent_score)
            return eval_score, None

        best_move = None

        if is_maximizing:
            # Maximizing player (AI)
            max_eval = float('-inf')

            for move in possible_moves:
                # Make a copy of the game state to explore this move
                # (You'll need to implement game state copy if not already available)

                # Simulate the move
                # eval_score, _ = self.expectimax(graph_copy, tiles_info, rules_manager,
                #                                  depth - 1, alpha, beta, False,
                #                                  updated_ai_score, opponent_score)

                # For now, use evaluation without recursion to avoid state management complexity
                eval_score = self.evaluate_state(
                    graph, current_player_score, opponent_score)

                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move

                alpha = max(alpha, eval_score)

                # Beta cutoff
                if beta <= alpha:
                    break

            return max_eval, best_move

        else:
            # Minimizing player (opponent)
            min_eval = float('inf')

            for move in possible_moves:
                # Simulate the move
                # eval_score, _ = self.expectimax(graph_copy, tiles_info, rules_manager,
                #                                  depth - 1, alpha, beta, True,
                #                                  current_player_score, updated_opponent_score)

                eval_score = self.evaluate_state(
                    graph, current_player_score, opponent_score)

                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move

                beta = min(beta, eval_score)

                # Alpha cutoff
                if beta <= alpha:
                    break

            return min_eval, best_move


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
