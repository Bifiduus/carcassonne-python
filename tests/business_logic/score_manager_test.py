from types import SimpleNamespace

from carcassonne.business_logic.player import Player
from carcassonne.business_logic.score_manager import ScoreManager
from carcassonne.datas.meeple_data import Meeple
from carcassonne.datas.tiles_info import TilesInfo


class DummyVertex:
    def __init__(
        self,
        position=(0, 0),
        name="CFFF",
        orientation=0,
        middle="",
        neighbors=None,
    ) -> None:
        self.position = position
        self.name = name
        self.orientation = orientation
        self.middle = middle
        self.neighbors = dict(neighbors or {})

    def get_position(self):
        return self.position


def build_players() -> dict[int, Player]:
    return {
        0: Player(0, "Alice", "red"),
        1: Player(1, "Bob", "blue"),
        2: Player(2, "Cara", "yellow"),
    }


def build_graph(**overrides):
    graph = {
        "lands_components": {},
        "vertices": {},
        "meeples": [],
        "tiles_dict": TilesInfo().tiles,
    }
    graph.update(overrides)
    return SimpleNamespace(**graph)


def test_monastery_completion_and_surrounding_count_cover_complete_and_incomplete_cases() -> None:
    complete_vertices = {0: DummyVertex((0, 0), name="FFFF")}
    tile_id = 1
    complete_vertices[tile_id] = DummyVertex((5, 5), name="FFFF")
    for index, position in enumerate(
        {
            (4, 4),
            (4, 5),
            (4, 6),
            (5, 4),
            (5, 6),
            (6, 4),
            (6, 5),
            (6, 6),
        },
        start=2,
    ):
        complete_vertices[index] = DummyVertex(position)

    complete_graph = build_graph(
        lands_components={"M": {"M1": [(tile_id, ["C"])]}},
        vertices=complete_vertices,
    )

    assert ScoreManager.is_component_complete("X", "X1", complete_graph) is False
    assert ScoreManager.is_component_complete("M", "M9", complete_graph) is False
    assert ScoreManager._count_surrounding_tiles(tile_id, complete_graph) == 8
    assert ScoreManager.is_component_complete("M", "M1", complete_graph) is True

    incomplete_graph = build_graph(
        lands_components={"M": {"M1": [(tile_id, ["C"])]}},
        vertices={
            tile_id: DummyVertex((0, 0), name="FFFF"),
            2: DummyVertex((0, 1)),
            3: DummyVertex((1, 0)),
        },
    )

    assert ScoreManager._count_surrounding_tiles(tile_id, incomplete_graph) == 2
    assert ScoreManager.is_component_complete("M", "M1", incomplete_graph) is False
    assert ScoreManager._count_surrounding_tiles(999, incomplete_graph) == 0
    assert ScoreManager._is_monastery_complete([], incomplete_graph) is False


def test_convert_tile_direction_to_board_direction_covers_rotation_and_fallbacks() -> None:
    graph = build_graph(
        vertices={1: DummyVertex(name="CFFF", orientation=1)},
    )

    assert (
        ScoreManager._convert_tile_direction_to_board_direction(1, "N", graph)
        == "E"
    )
    assert (
        ScoreManager._convert_tile_direction_to_board_direction(1, "X", graph)
        is None
    )
    assert (
        ScoreManager._convert_tile_direction_to_board_direction(99, "N", graph)
        is None
    )

    unknown_tile_graph = build_graph(
        vertices={1: DummyVertex(name="UNKNOWN", orientation=0)},
        tiles_dict={},
    )
    assert (
        ScoreManager._convert_tile_direction_to_board_direction(
            1, "W", unknown_tile_graph
        )
        == "W"
    )


def test_is_edge_component_complete_detects_free_edges_and_closed_components() -> None:
    assert ScoreManager._is_edge_component_complete([], build_graph()) is False

    closed_graph = build_graph(
        vertices={
            1: DummyVertex(name="FRFR", neighbors={1: 2}),
            2: DummyVertex(name="FRFR", neighbors={3: 1}),
        }
    )
    assert (
        ScoreManager._is_edge_component_complete(
            [(1, ["E"]), (2, ["W"])], closed_graph
        )
        is True
    )

    free_edge_graph = build_graph(
        vertices={1: DummyVertex(name="FRFR", neighbors={})}
    )
    assert (
        ScoreManager._is_edge_component_complete([(1, ["E"])], free_edge_graph)
        is False
    )

    outside_neighbor_graph = build_graph(
        vertices={1: DummyVertex(name="FRFR", neighbors={1: 99})}
    )
    assert (
        ScoreManager._is_edge_component_complete(
            [(1, ["E"])], outside_neighbor_graph
        )
        is False
    )


def test_award_majority_score_handles_ties_and_absent_meeples() -> None:
    players = build_players()
    graph = build_graph(
        meeples=[
            Meeple(0, 1, 0, "C1"),
            Meeple(1, 2, 0, "C1"),
            Meeple(2, 3, 0, "R1"),
        ]
    )

    ScoreManager._award_majority_score("C1", 6, graph, players)
    ScoreManager._award_majority_score("UNKNOWN", 9, graph, players)

    assert players[0].get_score_int() == 6
    assert players[1].get_score_int() == 6
    assert players[2].get_score_int() == 0


def test_count_helpers_and_return_component_meeples_update_players_and_graph() -> None:
    players = build_players()
    original_meeples = {player_id: player.get_meeples() for player_id, player in players.items()}
    graph = build_graph(
        vertices={
            1: DummyVertex(middle="b"),
            2: DummyVertex(middle=""),
            3: DummyVertex(middle="b"),
        },
        meeples=[
            Meeple(0, 1, 0, "C1"),
            Meeple(1, 2, 0, "C1"),
            Meeple(1, 3, 0, "C1"),
            Meeple(2, 4, 0, "R1"),
        ],
    )

    assert ScoreManager.count_meeples_on_component("C1", graph) == {0: 1, 1: 2}
    assert ScoreManager.count_banners_on_tiles([1, 2, 3], graph) == 2

    ScoreManager._return_component_meeples_to_players("C1", graph, players)

    assert len(graph.meeples) == 1
    assert graph.meeples[0].lands_components == "R1"
    assert players[0].get_meeples() == original_meeples[0] + 1
    assert players[1].get_meeples() == original_meeples[1] + 2
    assert players[2].get_meeples() == original_meeples[2]


def test_score_methods_apply_expected_points() -> None:
    players = build_players()
    graph = build_graph(
        vertices={
            1: DummyVertex(middle="b"),
            2: DummyVertex(middle=""),
            3: DummyVertex(position=(0, 0), name="FFFF"),
            4: DummyVertex(position=(0, 1)),
            5: DummyVertex(position=(1, 0)),
            6: DummyVertex(position=(1, 1)),
        },
        meeples=[
            Meeple(0, 1, 0, "R1"),
            Meeple(1, 1, 0, "C1"),
            Meeple(2, 3, 8, "M1"),
            Meeple(0, 1, 0, "R2"),
            Meeple(1, 1, 0, "C2"),
        ],
    )

    ScoreManager._score_road_complete([(1, ["E"]), (2, ["W"])], "R1", graph, players)
    ScoreManager._score_city_complete([(1, ["N"]), (2, ["S"])], "C1", graph, players)
    ScoreManager._score_monastery_complete([(3, ["C"])], "M1", graph, players)
    ScoreManager._score_road_incomplete([(1, ["E"]), (2, ["W"])], "R2", graph, players)
    ScoreManager._score_city_incomplete([(1, ["N"]), (2, ["S"])], "C2", graph, players)

    assert players[0].get_score_int() == 2 + 2
    assert players[1].get_score_int() == 6 + 3
    assert players[2].get_score_int() == 9


def test_score_monastery_incomplete_requires_exactly_one_meeple() -> None:
    players = build_players()
    graph = build_graph(
        vertices={
            1: DummyVertex(position=(0, 0), name="FFFF"),
            2: DummyVertex(position=(0, 1)),
            3: DummyVertex(position=(1, 0)),
            4: DummyVertex(position=(1, 1)),
        },
        meeples=[Meeple(0, 1, 8, "M1")],
    )

    ScoreManager._score_monastery_incomplete([(1, ["C"])], "M1", graph, players)
    assert players[0].get_score_int() == 4

    graph.meeples.append(Meeple(1, 1, 8, "M1"))
    ScoreManager._score_monastery_incomplete([(1, ["C"])], "M1", graph, players)

    assert players[0].get_score_int() == 4
    assert players[1].get_score_int() == 0


def test_count_adjacent_completed_cities_and_field_scoring_use_unique_complete_neighbors(
    monkeypatch,
) -> None:
    players = build_players()
    graph = build_graph(
        vertices={
            1: DummyVertex(neighbors={0: 2, 1: 3, 2: 4}),
            2: DummyVertex(),
            3: DummyVertex(),
            4: DummyVertex(),
        },
        lands_components={
            "C": {
                "C1": [(2, ["N"]), (3, ["S"])],
                "C2": [(4, ["N"])],
            }
        },
        meeples=[Meeple(0, 1, 0, "F1")],
    )

    monkeypatch.setattr(
        ScoreManager,
        "is_component_complete",
        staticmethod(lambda terrain, name, graph: name == "C1"),
    )

    count = ScoreManager._count_adjacent_completed_cities([(1, ["NW"])], graph)
    ScoreManager._score_field([(1, ["NW"])], "F1", graph, players)

    assert count == 1
    assert players[0].get_score_int() == 3


def test_score_end_of_turn_and_end_of_game_dispatch_only_relevant_components(monkeypatch) -> None:
    graph = build_graph(
        lands_components={
            "R": {"R1": [(1, ["E"])]},
            "C": {"C1": [(2, ["N"])]},
            "M": {"M1": [(3, ["C"])]},
            "F": {"F1": [(4, ["NW"])]},
        }
    )
    players = build_players()
    completed = {"R:R1", "C:C1"}
    calls: list[tuple[str, str]] = []

    monkeypatch.setattr(
        ScoreManager,
        "is_component_complete",
        staticmethod(lambda terrain, name, graph: name in {"C1", "M1"}),
    )
    monkeypatch.setattr(
        ScoreManager,
        "_score_road_complete",
        staticmethod(lambda component, name, graph, players: calls.append(("turn-road", name))),
    )
    monkeypatch.setattr(
        ScoreManager,
        "_score_city_complete",
        staticmethod(lambda component, name, graph, players: calls.append(("turn-city", name))),
    )
    monkeypatch.setattr(
        ScoreManager,
        "_score_monastery_complete",
        staticmethod(lambda component, name, graph, players: calls.append(("turn-monastery", name))),
    )
    monkeypatch.setattr(
        ScoreManager,
        "_return_component_meeples_to_players",
        staticmethod(lambda name, graph, players: calls.append(("return", name))),
    )

    ScoreManager.score_end_of_turn(graph, players, scored_components=completed)

    monkeypatch.setattr(
        ScoreManager,
        "_score_road_incomplete",
        staticmethod(lambda component, name, graph, players: calls.append(("end-road", name))),
    )
    monkeypatch.setattr(
        ScoreManager,
        "_score_city_incomplete",
        staticmethod(lambda component, name, graph, players: calls.append(("end-city", name))),
    )
    monkeypatch.setattr(
        ScoreManager,
        "_score_monastery_incomplete",
        staticmethod(lambda component, name, graph, players: calls.append(("end-monastery", name))),
    )
    monkeypatch.setattr(
        ScoreManager,
        "_score_field",
        staticmethod(lambda component, name, graph, players: calls.append(("field", name))),
    )

    ScoreManager.score_end_of_game(graph, players)

    assert calls == [
        ("turn-monastery", "M1"),
        ("return", "M1"),
        ("end-road", "R1"),
        ("field", "F1"),
    ]
