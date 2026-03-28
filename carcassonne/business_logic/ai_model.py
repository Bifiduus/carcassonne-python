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
    AIModelManager,
    initialize_ai,
    is_ai_player,
    get_ai_move,
)
