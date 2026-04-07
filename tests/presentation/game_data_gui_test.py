import pytest
from types import SimpleNamespace
from unittest.mock import Mock

pytest.importorskip("gi")

from carcassonne.presentation.gui.game_data_gui import GameDataGui


class DummyTilesInfo:
    direction_dict = {"N": 0, "E": 1, "S": 2, "W": 3}


class DummyGame:
    def __init__(self, hint_move, adjacent_position=(1, 2)) -> None:
        self.provide_hint = Mock(return_value=hint_move)
        self.get_adjacent_position = Mock(return_value=adjacent_position)
        self.game_data = SimpleNamespace(tiles_info=DummyTilesInfo())


def test_provide_hint_sets_hint_tile_and_requests_redraw() -> None:
    game = DummyGame("CFFF/0N0")
    gui_data = GameDataGui(game, client_service=Mock(), server_service=Mock())
    gui_data.board_view = SimpleNamespace(queue_draw=Mock())

    hint_move = gui_data.provide_hint()

    assert hint_move == "CFFF/0N0"
    game.provide_hint.assert_called_once()
    game.get_adjacent_position.assert_called_once_with(vertex_id=0, side=0)
    assert gui_data.hint_tile == {
        "id": -1,
        "x": 1,
        "y": 2,
        "name": "CFFF",
        "middle": None,
        "orientation": 0,
        "meeple": "",
    }
    gui_data.board_view.queue_draw.assert_called_once()


def test_provide_hint_returns_empty_without_hint_tile() -> None:
    game = DummyGame("")
    gui_data = GameDataGui(game, client_service=Mock(), server_service=Mock())
    gui_data.board_view = SimpleNamespace(queue_draw=Mock())

    hint_move = gui_data.provide_hint()

    assert hint_move == ""
    assert game.provide_hint.called
    game.get_adjacent_position.assert_not_called()
    assert gui_data.hint_tile is None
    gui_data.board_view.queue_draw.assert_not_called()
