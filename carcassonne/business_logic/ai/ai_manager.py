"""Legacy AIModelManager and module-level helpers."""

from __future__ import annotations

from typing import Optional

from carcassonne.business_logic.interfaces.i_graph_data import IGraphData
from carcassonne.business_logic.interfaces.i_tiles_info import ITilesInfo
from carcassonne.business_logic.rules_manager import RulesManager
from carcassonne.datas.history import MoveRecord
from carcassonne.business_logic.ai.expectimax_player import ExpectimaxPlayer


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
