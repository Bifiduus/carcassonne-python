from types import SimpleNamespace

import pytest

from carcassonne.business_logic.heuristic_short_term import (
    ShortTermWeights,
    _component_controllers,
    _component_meeple_counts,
    _component_tile_count,
    _compress_to_star_bounds,
    _count_open_edges,
    _estimate_completion_points,
    _find_player,
    _get_player_meeples,
    _get_player_score,
    _imminence_factor,
    _player_component_presence,
    _remaining_to_completion,
    _short_term_profile,
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


def build_short_term_state():
    players = {
        0: DummyPlayer(0, score=12, meeples=5),
        1: DummyPlayer(1, score=7, meeples=6),
    }
    graph = DummyGraph(
        lands_components={
            "C": {"C1": [(1, ["N", "E"])]},
            "R": {"R1": [(2, ["E"])]},
            "M": {"M1": [(3, ["C"])]},
        },
        vertices={
            1: DummyVertex(name="CCFF", middle="b"),
            2: DummyVertex(name="FRFR"),
            3: DummyVertex(name="FFFF", position=(0, 0)),
            4: DummyVertex(position=(0, 1)),
            5: DummyVertex(position=(1, 0)),
            6: DummyVertex(position=(1, 1)),
        },
        meeples=[
            Meeple(0, 1, 0, "C1"),
            Meeple(1, 1, 1, "C1"),
            Meeple(0, 2, 2, "R1"),
            Meeple(1, 3, 8, "M1"),
            SimpleNamespace(player_id=2, lands_components=None),
        ],
    )
    return SimpleNamespace(game_data=SimpleNamespace(players=players, graph=graph))


def test_short_term_helpers_cover_counts_points_and_completion_estimates() -> None:
    game_state = build_short_term_state()
    graph = game_state.game_data.graph
    counts = _component_meeple_counts(game_state)

    assert _find_player(game_state, 0) is game_state.game_data.players[0]
    assert _find_player(game_state, 99) is None
    assert _get_player_score(game_state, 0) == 12.0
    assert _get_player_score(game_state, 99) == 0.0
    assert _get_player_meeples(game_state, 1) == 6.0
    assert _get_player_meeples(game_state, 99) == 0.0
    assert counts == {"C1": {0: 1, 1: 1}, "R1": {0: 1}, "M1": {1: 1}}
    assert _component_controllers("C1", counts) == [0, 1]
    assert _component_controllers("unknown", counts) == []
    assert _component_tile_count([(1, ["N"]), (1, ["E"]), (2, ["W"])]) == 2.0
    assert _estimate_completion_points("R", [(2, ["E"])], graph) == 1.0
    assert _estimate_completion_points("C", [(1, ["N", "E"])], graph) == 4.0
    assert _estimate_completion_points("M", [(3, ["C"])], graph) == 9.0
    assert _estimate_completion_points("F", [(1, ["NW"])], graph) == 0.0
    assert _count_open_edges([(1, ["N", "E", "X"]), (99, ["W"])], graph) == 2
    assert _count_open_edges([(2, ["E"])], graph) == 1
    assert _remaining_to_completion("C", [(1, ["N", "E"])], graph) == 2
    assert _remaining_to_completion("M", [(3, ["C"])], graph) == 5
    assert _remaining_to_completion("M", [], graph) == 8
    assert _imminence_factor(0) == 0.0
    assert _imminence_factor(1) == 1.0
    assert _imminence_factor(2) == 0.45
    assert _imminence_factor(3) == 0.0
    assert _player_component_presence("C1", counts, 0) == 1
    assert _player_component_presence("C1", counts, 2) == 0


def test_short_term_profile_and_features_reflect_ready_and_pressure_components() -> None:
    game_state = build_short_term_state()

    player_profile = _short_term_profile(game_state, 0)
    opponent_profile = _short_term_profile(game_state, 1)
    features = extract_features(game_state, 0, 1)

    assert player_profile["score"] == 12.0
    assert player_profile["available_meeples"] == 5.0
    assert player_profile["imminent_points"] == pytest.approx(1.9)
    assert player_profile["imminent_meeple_returns"] == pytest.approx(1.45)
    assert player_profile["ready_components"] == 1.0
    assert player_profile["pressure_components"] == 0.5

    assert opponent_profile["score"] == 7.0
    assert opponent_profile["available_meeples"] == 6.0
    assert opponent_profile["imminent_points"] == pytest.approx(0.9)
    assert opponent_profile["imminent_meeple_returns"] == pytest.approx(0.45)
    assert opponent_profile["ready_components"] == 0.0
    assert opponent_profile["pressure_components"] == 0.5

    assert features == {
        "score_diff": 5.0,
        "available_meeples_diff": -1.0,
        "imminent_points_diff": pytest.approx(1.0),
        "imminent_meeple_returns_diff": pytest.approx(1.0),
        "ready_components_diff": 1.0,
        "pressure_components_diff": 0.0,
    }


def test_short_term_compression_and_evaluation_are_well_behaved() -> None:
    game_state = build_short_term_state()
    weights = ShortTermWeights(
        score_diff=0.0,
        available_meeples_diff=0.0,
        imminent_points_diff=50.0,
        imminent_meeple_returns_diff=0.0,
        ready_components_diff=30.0,
        pressure_components_diff=0.0,
    )

    assert _compress_to_star_bounds(20.0) > 0
    assert _compress_to_star_bounds(-20.0) < 0
    with pytest.raises(ValueError, match="Compression scale must be > 0"):
        _compress_to_star_bounds(5.0, scale=0.0)

    assert evaluate_state(game_state, 0, 1, weights) > 0
    assert evaluate_state(game_state, 1, 0, weights) < 0
