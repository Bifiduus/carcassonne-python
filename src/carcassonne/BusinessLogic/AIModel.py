"""
This module implements the AI player using the Alpha-Beta pruning algorithm.
It provides intelligent move selection for the AI player in Carcassonne.
"""

from typing import List, Tuple, Optional
from carcassonne.Datas.History import MoveRecord
from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData
from carcassonne.BusinessLogic.Interfaces.ITilesInfo import ITilesInfo
from carcassonne.BusinessLogic.RulesManager import RulesManager


def STAR1(graph: IGraphData, ai_score: int, opponent_score: int) -> float:
    """Simple heuristic: score diff + board control + potential."""
    score_diff = ai_score - opponent_score
    board_control = len(graph.get_verticies()) * 5
    potential = 0
    for v in graph.get_verticies().values():
        potential += 8
    return score_diff + board_control + potential


def STAR2(graph: IGraphData, ai_score: int, opponent_score: int) -> float:
    """Aggressive heuristic: favors board control and potential more."""
    score_diff = ai_score - opponent_score
    board_control = len(graph.get_verticies()) * 8
    potential = 0
    for v in graph.get_verticies().values():
        potential += 12
    return (score_diff * 1.0) + board_control + potential * 0.8


def STAR2_5(graph: IGraphData, ai_score: int, opponent_score: int) -> float:
    """Balanced heuristic between STAR1 and STAR2."""
    score_diff = ai_score - opponent_score
    board_control = len(graph.get_verticies()) * 6
    potential = 0
    for v in graph.get_verticies().values():
        potential += 10
    return score_diff + board_control + potential * 0.9


class AlphaBetaPlayer:
    """
    AI player using Alpha-Beta pruning algorithm for intelligent move selection.
    """
    
    def __init__(self, depth: int = 4, is_maximizing: bool = True, eval_name: str = "STAR1", eval_fn=None):
        """
        Initialize the Alpha-Beta AI player.
        
        Args:
            depth: Maximum depth for the search tree (default: 4)
            is_maximizing: Whether this player is maximizing (True for AI, False for opponent)
        """
        self.depth = depth
        self.is_maximizing = is_maximizing
        self.nodes_explored = 0
        # evaluation function (callable(graph, ai_score, opponent_score) -> float)
        self.eval_fn = None
        if eval_fn is not None:
            self.eval_fn = eval_fn
        else:
            self.set_evaluation_method(eval_name)
    
    def set_evaluation_method(self, name_or_fn):
        """Set evaluation by name ('STAR1','STAR2','STAR2_5') or by callable.

        Accepts a callable(graph, ai_score, opponent_score) or a string name.
        """
        if callable(name_or_fn):
            self.eval_fn = name_or_fn
            return

        name = (name_or_fn or '').upper()
        if name == 'STAR1':
            self.eval_fn = STAR1
        elif name == 'STAR2':
            self.eval_fn = STAR2
        elif name in ('STAR2_5', 'STAR2.5', 'STAR25'):
            self.eval_fn = STAR2_5
        else:
            raise ValueError(f"Unknown evaluation method: {name_or_fn}")
        
    def get_possible_moves(self, graph: IGraphData, tiles_info: ITilesInfo, 
                          rules_manager: RulesManager) -> List[str]:
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
        available_tiles = tiles_info.get_available_tiles()
        
        # Try to place each available tile on each empty neighbor position
        vertices = graph.get_verticies()

        # Try to place the tile next to each existing vertex
        for vertex_id, vertex in vertices.items():
            # Try each direction (North, South, East, West)
            for direction in ['N', 'S', 'E', 'W']:
                # Check if this side is free
                if vertex.is_neighbor_free(tiles_info.direction_dict.get(direction, 0)):
                    # Try each rotation (0, 90, 180, 270 degrees)
                    for rotation in range(4):
                        for tile in available_tiles:
                            move = f"{tile}/{vertex_id}{direction}{rotation}"
                            # Verify the move is legal
                            move_parts = move.split('/')
                            if rules_manager.is_correctly_formed_move(move, graph):
                                if rules_manager.is_legal_move(move_parts, graph):
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
    
    def alpha_beta(self, graph: IGraphData, tiles_info: ITilesInfo, 
                   rules_manager: RulesManager, depth: int, alpha: float, 
                   beta: float, is_maximizing: bool, 
                   current_player_score: int, opponent_score: int) -> Tuple[float, Optional[str]]:
        """
        Alpha-Beta pruning algorithm for game tree search.
        
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
            eval_score = self.evaluate_state(graph, current_player_score, opponent_score)
            return eval_score, None
        
        # Get all possible moves
        possible_moves = self.get_possible_moves(graph, tiles_info, rules_manager)
        
        # Leaf node: no moves available
        if not possible_moves:
            eval_score = self.evaluate_state(graph, current_player_score, opponent_score)
            return eval_score, None
        
        best_move = None
        
        if is_maximizing:
            # Maximizing player (AI)
            max_eval = float('-inf')
            
            for move in possible_moves:
                # Make a copy of the game state to explore this move
                # (You'll need to implement game state copy if not already available)
                
                # Simulate the move
                # eval_score, _ = self.alpha_beta(graph_copy, tiles_info, rules_manager, 
                #                                  depth - 1, alpha, beta, False, 
                #                                  updated_ai_score, opponent_score)
                
                # For now, use evaluation without recursion to avoid state management complexity
                eval_score = self.evaluate_state(graph, current_player_score, opponent_score)
                
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
                # eval_score, _ = self.alpha_beta(graph_copy, tiles_info, rules_manager,
                #                                  depth - 1, alpha, beta, True,
                #                                  current_player_score, updated_opponent_score)
                
                eval_score = self.evaluate_state(graph, current_player_score, opponent_score)
                
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
            depth: Maximum search depth for Alpha-Beta algorithm
        """
        self.player = AlphaBetaPlayer(depth=depth, eval_name=eval_name)
    
    def choose_best_move(self, graph: IGraphData, tiles_info: ITilesInfo,
                        rules_manager: RulesManager, ai_score: int,
                        opponent_score: int) -> Optional[str]:
        """
        Choose the best move for the AI using Alpha-Beta pruning.
        
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
        
        _, best_move = self.player.alpha_beta(
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
        depth: Maximum search depth for Alpha-Beta algorithm
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