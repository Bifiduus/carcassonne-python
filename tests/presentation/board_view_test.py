import pytest
pytest.importorskip("gi")
from types import SimpleNamespace
from unittest.mock import Mock

from carcassonne.presentation.gui.board_view import BoardView


class DummyCurrentTile:
    def __init__(self):
        self.current_tile = "CFFF"
        self.move = None
        self.x = None
        self.y = None


def make_board_view(monkeypatch):
    monkeypatch.setattr("carcassonne.presentation.gui.board_view.Gtk.DrawingArea.__init__", lambda self: None)
    monkeypatch.setattr("carcassonne.presentation.gui.board_view.Gtk.DrawingArea.set_draw_func", lambda self, func: None)
    monkeypatch.setattr("carcassonne.presentation.gui.board_view.Gtk.DrawingArea.set_content_width", lambda self, width: None)
    monkeypatch.setattr("carcassonne.presentation.gui.board_view.Gtk.DrawingArea.set_content_height", lambda self, height: None)
    monkeypatch.setattr("carcassonne.presentation.gui.board_view.Gtk.DrawingArea.add_controller", lambda self, controller: None)
    monkeypatch.setattr("carcassonne.presentation.gui.board_view.Gtk.DrawingArea.set_focusable", lambda self, focusable: None)
    monkeypatch.setattr("carcassonne.presentation.gui.board_view.Gtk.DrawingArea.grab_focus", lambda self: None)
    monkeypatch.setattr("carcassonne.presentation.gui.board_view.BoardView._setup_input_controllers", lambda self: None)
    return BoardView(game_data=SimpleNamespace(game=SimpleNamespace()))


def test_create_move_str_builds_expected_move(monkeypatch) -> None:
    board_view = make_board_view(monkeypatch)
    board_view.game_data = SimpleNamespace(
        game=SimpleNamespace(get_close_neighbors=Mock(return_value=(12, 2))),
        current_tile=DummyCurrentTile(),
        current_orientation=1,
    )

    move_str = board_view._create_move_str(0, 0)

    assert move_str == "CFFF/12S1"


def test_create_move_str_returns_none_when_no_close_neighbor(monkeypatch) -> None:
    board_view = make_board_view(monkeypatch)
    board_view.game_data = SimpleNamespace(
        game=SimpleNamespace(get_close_neighbors=Mock(return_value=(None, None))),
        current_tile=DummyCurrentTile(),
        current_orientation=0,
    )

    assert board_view._create_move_str(0, 0) is None


def test_set_tile_placement_updates_tile_move_and_coordinates(monkeypatch) -> None:
    board_view = make_board_view(monkeypatch)
    current_tile = DummyCurrentTile()
    board_view.game_data = SimpleNamespace(current_tile=current_tile)

    board_view._set_tile_placement(3, 4, "CFFF/12S1")

    assert current_tile.move == "CFFF/12S1"
    assert current_tile.x == 3
    assert current_tile.y == 4
