"""Heuristic module isolated from search algorithms.
"""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class HeuristicWeights:
    """Weights used by the linear evaluation function."""

    score_diff: float = 100.0
    meeple_diff: float = 10.0
    latent_score_diff: float = 10.0
    incomplete_city_tiles_diff: float = 1.25
    risky_fields_lt3_diff: float = -40.0


DEFAULT_WEIGHTS = HeuristicWeights()


def extract_features(state: Any, player_id: int, opponent_id: int) -> dict[str, float]:
    """Return heuristic features (player - opponent).
    """
    _ = (state, player_id, opponent_id)
    return {
        "score_diff": 0.0,
        "meeple_diff": 0.0,
        "latent_score_diff": 0.0,
        "incomplete_city_tiles_diff": 0.0,
        "risky_fields_lt3_diff": 0.0,
    }


def evaluate_state(state: Any, player_id: int, opponent_id: int, weights: HeuristicWeights = DEFAULT_WEIGHTS) -> float:
    """Linear heuristic evaluation based on extracted features."""
    features = extract_features(state, player_id, opponent_id)
    return (
        weights.score_diff * features["score_diff"]
        + weights.meeple_diff * features["meeple_diff"]
        + weights.latent_score_diff * features["latent_score_diff"]
        + weights.incomplete_city_tiles_diff * features["incomplete_city_tiles_diff"]
        + weights.risky_fields_lt3_diff * features["risky_fields_lt3_diff"]
    )
