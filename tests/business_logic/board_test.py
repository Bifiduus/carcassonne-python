from types import SimpleNamespace

from carcassonne.business_logic.game.board import Board
from carcassonne.business_logic.player import Player
from carcassonne.datas.graph_data import GraphData
from carcassonne.datas.history import History
from carcassonne.datas.starting_tile import initialize_starting_tile
from carcassonne.datas.tiles_info import TilesInfo


def build_board_runtime():
    graph = GraphData()
    initialize_starting_tile(graph)
    return (
        Board(),
        graph,
        TilesInfo(),
        History(),
        {
            0: Player(0, "Alice", "red"),
            1: Player(1, "Bob", "blue"),
        },
    )


def test_add_tile_to_board_places_tile_updates_history_and_consumes_tile() -> None:
    board, graph, tiles_info, history, players = build_board_runtime()
    initial_count = tiles_info.tiles_count["FFFF/m"]

    board.add_tile_to_board(
        "FFFF/m/0N0",
        graph,
        tiles_info,
        history,
        players,
        [0, 1],
        players[0],
    )

    vertex = graph.get_vertex(1)
    assert vertex is not None
    assert vertex.get_name() == "FFFF"
    assert vertex.get_middle() == "m"
    assert vertex.get_position() == (0, -1)
    assert tiles_info.tiles_count["FFFF/m"] == initial_count - 1
    assert [record.move_str for record in history.past_moves] == ["FFFF/m/0N0"]
    assert history.future_moves == []


def test_add_tile_to_board_places_meeple_on_available_component() -> None:
    board, graph, tiles_info, history, players = build_board_runtime()

    board.add_tile_to_board(
        "CFFF/0N0/N",
        graph,
        tiles_info,
        history,
        players,
        [0, 1],
        players[0],
    )

    assert len(graph.meeples) == 1
    assert graph.meeples[0].player_id == 0
    assert players[0].get_meeples() == 6
    assert history.past_moves[-1].move_str == "CFFF/0N0/N"


def test_add_tile_to_board_normalizes_meeple_position_for_rotated_tiles() -> None:
    board, graph, tiles_info, history, players = build_board_runtime()

    board.add_tile_to_board(
        "CFFF/0N2/N",
        graph,
        tiles_info,
        history,
        players,
        [0, 1],
        players[0],
    )

    assert len(graph.meeples) == 1
    assert graph.meeples[0].get_position_label() == "S"
    assert history.past_moves[-1].move_str == "CFFF/0N2/N"


def test_add_tile_to_board_returns_early_when_target_position_is_missing() -> None:
    board = Board()
    graph = SimpleNamespace(
        get_adjacent_position=lambda vertex_id, side: None,
        get_vertices=lambda: {},
    )
    tiles_info = SimpleNamespace(direction_dict={"N": 0})
    history = History()
    players = {0: Player(0, "Alice", "red")}

    board.add_tile_to_board(
        "CFFF/0N0",
        graph,
        tiles_info,
        history,
        players,
        [0],
        players[0],
    )

    assert history.past_moves == []


def test_remove_tile_from_board_restores_tile_and_returns_meeple_to_owner() -> None:
    board, graph, tiles_info, history, players = build_board_runtime()
    initial_count = tiles_info.tiles_count["CFFF"]

    board.add_tile_to_board(
        "CFFF/0N0/N",
        graph,
        tiles_info,
        history,
        players,
        [0, 1],
        players[0],
    )
    assert players[0].get_meeples() == 6

    board.remove_tile_from_board(
        "0:CFFF/0N0/N",
        graph,
        tiles_info,
        history,
        players,
    )

    assert graph.get_vertex(1) is None
    assert graph.meeples == []
    assert players[0].get_meeples() == 7
    assert tiles_info.tiles_count["CFFF"] == initial_count
