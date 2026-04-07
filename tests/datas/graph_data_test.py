import pytest

from carcassonne.business_logic.player import Player
from carcassonne.datas.graph_data import EAST_DIR, GraphData, Vertex, WEST_DIR
from carcassonne.datas.meeple_data import Meeple
from carcassonne.datas.starting_tile import (
    initialize_starting_tile,
    initialize_starting_tile_river,
)
from carcassonne.datas.tiles_info import TilesInfo


def create_vertex(vertex_id: int, name: str = "CRFR", orientation: int = 0) -> Vertex:
    tiles = TilesInfo().tiles
    return Vertex(
        id=vertex_id,
        name=name,
        middle="",
        tile_dict=tiles[name].tiles_lands,
        orientation=orientation,
        position=(0, 0),
    )


def test_vertex_neighbor_management_rotation_and_validation() -> None:
    vertex = create_vertex(0, "CRFR", orientation=5)

    assert vertex.get_orientation() == 1

    vertex.set_neighbor(EAST_DIR, 1)
    assert vertex.is_neighbor_free(EAST_DIR) is False
    assert vertex.get_neighbors() == {EAST_DIR: 1}

    vertex.remove_neighbor(EAST_DIR)
    assert vertex.is_neighbor_free(EAST_DIR) is True

    vertex.rotate(2)
    assert vertex.get_orientation() == 3
    assert vertex.get_matrix()[1][1] != ""

    with pytest.raises(ValueError):
        vertex.set_neighbor(9, 1)


def test_graph_data_adds_neighbors_positions_and_views() -> None:
    graph = GraphData()
    initialize_starting_tile(graph)
    graph.add_vertex(1, "CFFF", "", 0, (1, 0))

    assert graph.get_turn_number() == 2
    assert graph.get_neighbors(0)[EAST_DIR] == 1
    assert graph.get_neighbors(1)[WEST_DIR] == 0
    assert graph.get_adjacent_position(0, EAST_DIR) == (1, 0)
    assert graph.get_adjacent_position_from((0, 0), EAST_DIR) == (1, 0)
    assert graph.get_vertex_orientation(1) == 0

    vertices_data = graph.get_vertices_data()
    assert vertices_data[0]["name"] == "CRFR"
    assert vertices_data[1]["x"] == 1

    vertex_data = graph.get_vertex_data(graph.get_vertex(1))
    assert vertex_data[1]["name"] == "CFFF"

    assert graph.find_neighbor_at(0, 1) == (0, 2)


def test_graph_data_removes_vertices_and_meeples_cleanly() -> None:
    graph = GraphData()
    initialize_starting_tile(graph)
    graph.add_vertex(1, "CFFF", "", 0, (1, 0))
    graph.lands_components["C"]["C99"] = [(1, ["N"])]
    graph.lands_components["F"]["F99"] = [(1, ["S"])]

    player = Player(0, "Player 0", "green")
    player.meeples = 6
    meeple = Meeple(0, 1, 0, "C99")
    graph.add_meeple(meeple)

    graph.remove_meeple(1, {0: player})

    assert graph.get_meeples() == []
    assert player.get_meeples() == 7

    graph.remove_vertex(1)

    assert graph.get_vertex(1) is None
    assert graph.get_neighbors(0) == {}
    assert "C99" not in graph.lands_components["C"]
    assert "F99" not in graph.lands_components["F"]
    assert graph.get_turn_number() == 1


def test_graph_data_reset_and_error_paths() -> None:
    graph = GraphData()
    initialize_starting_tile_river(graph)
    graph.set_meeples([Meeple(1, 0, 8, "F1")])

    assert graph.get_meeples()[0].get_position_label() == "C"

    graph.reset_graph()

    assert graph.get_turn_number() == 0
    assert graph.get_vertices() == {}
    assert graph.get_meeples() == []
    assert set(graph.lands_components) == {"C", "R", "F", "M", "S"}
    assert graph.get_neighbors(42) == {}

    initialize_starting_tile(graph)

    with pytest.raises(ValueError):
        graph.get_adjacent_position(0, 99)
    with pytest.raises(ValueError):
        graph.get_adjacent_position_from((0, 0), 99)
    with pytest.raises(ValueError):
        graph.get_vertex_orientation(99)
    with pytest.raises(ValueError):
        graph.compute_neighbors(99)
    with pytest.raises(ValueError):
        graph.set_neighbor(0, EAST_DIR, 1)
    with pytest.raises(ValueError):
        graph.remove_vertex(99)


def test_starting_tile_helpers_initialize_expected_vertices_and_components() -> None:
    default_graph = GraphData()
    initialize_starting_tile(default_graph)

    assert default_graph.get_vertex(0).get_name() == "CRFR"
    assert default_graph.lands_components["C"]
    assert default_graph.lands_components["R"]
    assert default_graph.lands_components["F"]

    river_graph = GraphData()
    initialize_starting_tile_river(river_graph)

    assert river_graph.get_vertex(0).get_name() == "FFSF"
    assert river_graph.lands_components["S"]
