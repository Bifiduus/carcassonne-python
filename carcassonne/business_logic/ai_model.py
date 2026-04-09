"""
Backward-compatibility shim — all symbols live in carcassonne.business_logic.ai
"""

# Re-export everything so existing imports keep working unchanged.
from carcassonne.business_logic.ai import (  # noqa: F401
    RandomPlayer,
    ExpectimaxPlayer,
    IterativeDeepeningPlayer,
    MCTSNode,
    MCTSPlayer,
    DEFAULT_MCTS_ML_DIR,
    DEFAULT_MCTS_ML_MODEL_PATH,
)


def is_ai_player(play) -> bool:
    """Return whether a move record was produced by an AI player."""
    return bool(getattr(play, "is_ai_move", False))
