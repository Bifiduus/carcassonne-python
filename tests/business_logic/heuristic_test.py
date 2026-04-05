from types import SimpleNamespace

import pytest

from carcassonne.business_logic.heuristic import (
    HeuristicWeights,
    _component_controllers,
    _component_meeple_counts,
    _component_tile_count,
    _compress_to_star_bounds,
    _count_incomplete_city_tiles,
    _count_risky_fields_lt3_completed_cities,
    _estimate_latent_score,
    _find_player,
    _get_player_committed_meeples,
    _get_player_score,
    _is_city_component_incomplete,
    evaluate_state,
    extract_features,
)
from carcassonne.datas.meeple_data import Meeple


class DummyScore:
    def __init__(self, score=0):
        self.score = score


class DummyPlayer:
    def __init__(self, player_id, meeples=7, score=0):
        self.id = player_id
        self.meeples = meeples
        self._score = DummyScore(score)

    def get_id(self):
        return self.id

    def get_score(self):
        return self._score


class DummyGraph:
    def __init__(self, lands_components=None, meeples=None, vertices=None):
        self.lands_components = lands_components or {
            "C": {},
            "R": {},
            "M": {},
            "F": {},
        }
        self._meeples = list(meeples or [])
        self.vertices = vertices or {}

    def get_meeples(self):
        return list(self._meeples)

    def get_vertex(self, tile_id):
        return self.vertices.get(tile_id)


class DummyVertex:
    def __init__(self, neighbors=None):
        self.neighbors = dict(neighbors or {})

    def get_neighbors(self):
        return dict(self.neighbors)


class DummyGameData:
    def __init__(
        self,
        player_meeples=7,
        opponent_meeples=7,
        player_score=0,
        opponent_score=0,
        graph=None,
    ):
        self.players = {
            0: DummyPlayer(0, meeples=player_meeples, score=player_score),
            1: DummyPlayer(1, meeples=opponent_meeples, score=opponent_score),
        }
        self.graph = graph or DummyGraph()


class DummyGameState:
    def __init__(
        self,
        player_meeples=7,
        opponent_meeples=7,
        player_score=0,
        opponent_score=0,
        graph=None,
    ):
        self.game_data = DummyGameData(
            player_meeples,
            opponent_meeples,
            player_score,
            opponent_score,
            graph,
        )


def build_richer_state():
    graph = DummyGraph(
        lands_components={
            "C": {
                "C1": [(1, ["N"])],
                "C2": [(5, ["N"])],
            },
            "R": {"R1": [(3, ["E"])]},
            "M": {"M1": [(4, ["C"])]},
            "F": {"F1": [(5, ["NW"])]},
        },
        meeples=[
            Meeple(0, 1, 0, "C1"),
            Meeple(1, 5, 0, "C2"),
            Meeple(0, 3, 2, "R1"),
            Meeple(0, 5, 7, "F1"),
            SimpleNamespace(player_id=2, lands_components=None),
        ],
        vertices={
            1: DummyVertex(neighbors={}),
            3: DummyVertex(neighbors={}),
            5: DummyVertex(neighbors={0: 99}),
        },
    )
    return DummyGameState(
        player_meeples=5,
        opponent_meeples=7,
        player_score=10,
        opponent_score=4,
        graph=graph,
    )


def test_extract_features_treats_committed_meeples_as_positive():
    game_state = DummyGameState(player_meeples=6, opponent_meeples=7)

    features = extract_features(game_state, 0, 1)

    assert features["meeple_diff"] == 1.0


def test_evaluate_state_improves_when_only_meeple_commitment_changes():
    neutral_state = DummyGameState(player_meeples=7, opponent_meeples=7)
    committed_state = DummyGameState(player_meeples=6, opponent_meeples=7)
    weights = HeuristicWeights(
        score_diff=0.0,
        meeple_diff=10.0,
        latent_score_diff=0.0,
        incomplete_city_tiles_diff=0.0,
        risky_fields_lt3_diff=0.0,
    )

    neutral_eval = evaluate_state(neutral_state, 0, 1, weights)
    committed_eval = evaluate_state(committed_state, 0, 1, weights)

    assert committed_eval > neutral_eval


def test_heuristic_helpers_cover_lookup_counts_and_city_completion() -> None:
    game_state = build_richer_state()
    counts = _component_meeple_counts(game_state)

    assert _find_player(game_state, 0) is game_state.game_data.players[0]
    assert _find_player(game_state, 99) is None
    assert _get_player_score(game_state, 0) == 10.0
    assert _get_player_score(game_state, 99) == 0.0
    assert _get_player_committed_meeples(game_state, 0) == 2.0
    assert _get_player_committed_meeples(game_state, 99) == 0.0
    assert counts == {"C1": {0: 1}, "C2": {1: 1}, "R1": {0: 1}, "F1": {0: 1}}
    assert _component_controllers("C1", counts) == [0]
    assert _component_controllers("unknown", counts) == []
    assert _component_tile_count([(1, ["N"]), (1, ["E"]), (2, ["W"])]) == 2.0
    assert _is_city_component_incomplete(game_state.game_data.graph, [(1, ["N"])]) is True
    assert _is_city_component_incomplete(game_state.game_data.graph, [(5, ["N"])]) is False
    assert (
        _is_city_component_incomplete(game_state.game_data.graph, [(999, ["N"])])
        is True
    )


def test_heuristic_feature_extractors_reflect_latent_city_and_field_risk() -> None:
    game_state = build_richer_state()

    assert _count_incomplete_city_tiles(game_state, 0) == 1.0
    assert _count_incomplete_city_tiles(game_state, 1) == 0.0
    assert _count_risky_fields_lt3_completed_cities(game_state, 0) == 1.0
    assert _count_risky_fields_lt3_completed_cities(game_state, 1) == 0.0
    assert _estimate_latent_score(game_state, 0) == 2.0
    assert _estimate_latent_score(game_state, 1) == 1.0

    assert extract_features(game_state, 0, 1) == {
        "score_diff": 6.0,
        "meeple_diff": 2.0,
        "latent_score_diff": 1.0,
        "incomplete_city_tiles_diff": 1.0,
        "risky_fields_lt3_diff": 1.0,
    }


def test_heuristic_compression_and_evaluation_handle_sign_and_invalid_scale() -> None:
    game_state = build_richer_state()
    weights = HeuristicWeights(
        score_diff=5.0,
        meeple_diff=10.0,
        latent_score_diff=20.0,
        incomplete_city_tiles_diff=15.0,
        risky_fields_lt3_diff=-30.0,
    )

    assert _compress_to_star_bounds(15.0) > 0
    assert _compress_to_star_bounds(-15.0) < 0
    with pytest.raises(ValueError, match="Compression scale must be > 0"):
        _compress_to_star_bounds(1.0, scale=0.0)

    assert evaluate_state(game_state, 0, 1, weights) > 0
    assert evaluate_state(game_state, 1, 0, weights) < 0
