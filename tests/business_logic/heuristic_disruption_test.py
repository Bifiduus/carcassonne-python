from types import SimpleNamespace

import pytest

from carcassonne.business_logic.heuristic_disruption import (
    DisruptionWeights,
    _component_controllers,
    _component_meeple_counts,
    _compress_to_star_bounds,
    _contested_investment_value,
    _denied_majority_value,
    _find_player,
    _get_player_meeples,
    _get_player_score,
    _imminence_factor,
    _imminent_threat,
    _player_component_presence,
    _stall_factor,
    _trapped_meeples,
    evaluate_state,
    extract_features,
)
from carcassonne.datas.meeple_data import Meeple
from carcassonne.datas.tiles_info import TilesInfo


class DummyScore:
    def __init__(self, score: int) -> None:
        self.score = score


class DummyPlayer:
    def __init__(self, player_id: int, score: int, meeples: int) -> None:
        self.player_id = player_id
        self._score = DummyScore(score)
        self.meeples = meeples

    def get_id(self) -> int:
        return self.player_id

    def get_score(self) -> DummyScore:
        return self._score

    def get_meeples(self) -> int:
        return self.meeples


class DummyVertex:
    def __init__(
        self,
        name: str = "CFFF",
        orientation: int = 0,
        middle: str = "",
        neighbors=None,
        position=(0, 0),
    ) -> None:
        self.name = name
        self.orientation = orientation
        self.middle = middle
        self.neighbors = dict(neighbors or {})
        self.position = position

    def get_position(self):
        return self.position


class DummyGraph:
    def __init__(self, lands_components, vertices, meeples) -> None:
        self.lands_components = lands_components
        self.vertices = vertices
        self._meeples = meeples
        self.tiles_dict = TilesInfo().tiles

    def get_meeples(self):
        return list(self._meeples)


def build_disruption_state():
    players = {
        0: DummyPlayer(0, score=10, meeples=5),
        1: DummyPlayer(1, score=7, meeples=6),
    }
    graph = DummyGraph(
        lands_components={
            "C": {
                "C1": [(1, ["N", "E"])],
                "C2": [(2, ["N", "E", "S"])],
            },
            "R": {
                "R1": [(3, ["E"])],
                "R2": [(8, ["N", "E", "W"])],
            },
            "M": {"M1": [(4, ["C"])]},
        },
        vertices={
            1: DummyVertex(name="CCFF", middle="b"),
            2: DummyVertex(name="CFFF"),
            3: DummyVertex(name="FRFR"),
            4: DummyVertex(name="FFFF", position=(0, 0)),
            5: DummyVertex(position=(0, 1)),
            6: DummyVertex(position=(1, 0)),
            7: DummyVertex(position=(1, 1)),
            8: DummyVertex(name="FRFR"),
        },
        meeples=[
            Meeple(0, 1, 0, "C1"),
            Meeple(1, 1, 1, "C1"),
            Meeple(0, 2, 2, "C2"),
            Meeple(0, 3, 2, "R1"),
            Meeple(1, 4, 8, "M1"),
            Meeple(0, 8, 0, "R2"),
            Meeple(1, 8, 1, "R2"),
            Meeple(1, 8, 2, "R2"),
        ],
    )
    return SimpleNamespace(game_data=SimpleNamespace(players=players, graph=graph))


def test_disruption_helpers_cover_player_lookup_and_thresholds() -> None:
    game_state = build_disruption_state()
    counts = _component_meeple_counts(game_state)

    assert _find_player(game_state, 0) is game_state.game_data.players[0]
    assert _find_player(game_state, 99) is None
    assert _get_player_score(game_state, 0) == 10.0
    assert _get_player_score(game_state, 99) == 0.0
    assert _get_player_meeples(game_state, 1) == 6.0
    assert _get_player_meeples(game_state, 99) == 0.0
    assert counts["C1"] == {0: 1, 1: 1}
    assert counts["R2"] == {0: 1, 1: 2}
    assert _component_controllers("C1", counts) == [0, 1]
    assert _component_controllers("R2", counts) == [1]
    assert _player_component_presence("R2", counts, 1) == 2
    assert _player_component_presence("R2", counts, 2) == 0
    assert _imminence_factor(1) == 1.0
    assert _imminence_factor(2) == 0.45
    assert _stall_factor(1) == 0.0
    assert _stall_factor(2) == 0.35
    assert _stall_factor(3) == 0.70
    assert _stall_factor(4) == 1.0


def test_disruption_metrics_reflect_threats_traps_and_contests() -> None:
    game_state = build_disruption_state()

    assert _imminent_threat(game_state, 0) == pytest.approx(1.9)
    assert _imminent_threat(game_state, 1) == pytest.approx(0.9)
    assert _trapped_meeples(game_state, 0) == pytest.approx(1.75)
    assert _trapped_meeples(game_state, 1) == pytest.approx(2.75)
    assert _contested_investment_value(game_state, 0) == pytest.approx(3.05)
    assert _contested_investment_value(game_state, 1) == pytest.approx(2.4)
    assert _denied_majority_value(game_state, 0, 1) == pytest.approx(4.0)
    assert _denied_majority_value(game_state, 1, 0) == pytest.approx(4.7)


def test_disruption_feature_extraction_and_evaluation_are_consistent() -> None:
    game_state = build_disruption_state()
    weights = DisruptionWeights(
        score_diff=5.0,
        available_meeples_diff=0.0,
        trapped_meeples_diff=20.0,
        contested_value_diff=0.0,
        denied_majority_value_diff=0.0,
        threat_balance_diff=30.0,
    )

    features = extract_features(game_state, 0, 1)

    assert features["score_diff"] == 3.0
    assert features["available_meeples_diff"] == -1.0
    assert features["trapped_meeples_diff"] == pytest.approx(1.0)
    assert features["contested_value_diff"] == pytest.approx(-0.65)
    assert features["denied_majority_value_diff"] == pytest.approx(-0.7)
    assert features["threat_balance_diff"] == pytest.approx(1.0)

    assert _compress_to_star_bounds(25.0) > 0
    assert _compress_to_star_bounds(-25.0) < 0
    with pytest.raises(ValueError, match="Compression scale must be > 0"):
        _compress_to_star_bounds(1.0, scale=0.0)

    assert evaluate_state(game_state, 0, 1, weights) > 0
    assert evaluate_state(game_state, 1, 0, weights) < 0
