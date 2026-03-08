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


def _find_player(game_state: Any, player_id: int) -> Any | None:
    for player in game_state.players:
        if player.get_id() == player_id:
            return player
    return None


def _get_player_score(game_state: Any, player_id: int) -> float:
    player = _find_player(game_state, player_id)
    if player is None:
        return 0.0

    return float(player.get_score().score)


def _get_player_meeples(game_state: Any, player_id: int) -> float:
    player = _find_player(game_state, player_id)
    if player is None:
        return 0.0

    return float(player.meeples)


def extract_features(game_state: Any, player_id: int, opponent_id: int) -> dict[str, float]:
    """Return heuristic features (player - opponent).
    """
    score_diff = _get_player_score(game_state, player_id) - _get_player_score(game_state, opponent_id)
    meeple_diff = _get_player_meeples(game_state, player_id) - _get_player_meeples(game_state, opponent_id)
    return {
        "score_diff": score_diff,
        "meeple_diff": meeple_diff,
        "latent_score_diff": 0.0,
        "incomplete_city_tiles_diff": 0.0,
        "risky_fields_lt3_diff": 0.0,
    }


def evaluate_state(game_state: Any, player_id: int, opponent_id: int, weights: HeuristicWeights = DEFAULT_WEIGHTS) -> float:
    """Linear heuristic evaluation based on extracted features."""
    features = extract_features(game_state, player_id, opponent_id)
    return (
        weights.score_diff * features["score_diff"]
        + weights.meeple_diff * features["meeple_diff"]
        + weights.latent_score_diff * features["latent_score_diff"]
        + weights.incomplete_city_tiles_diff * features["incomplete_city_tiles_diff"]
        + weights.risky_fields_lt3_diff * features["risky_fields_lt3_diff"]
    )
