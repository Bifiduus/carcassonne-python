from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

pytest.importorskip("gi")

from carcassonne.presentation.gui import commands_handler_gui


class DummyGUI:
    def __init__(self):
        self.game_data = SimpleNamespace(
            provide_hint=Mock(),
            draw_tile=Mock(return_value="CFFF"),
            rotate_current_tile=Mock(),
            play_move_gui=Mock(),
        )
        self.tile_preview = SimpleNamespace(set_filename=Mock(), update_rotation=Mock())
        self.players_view = SimpleNamespace(refresh=Mock())
        self.update_preview_rotation = Mock()


def test_on_hint_delegates_to_game_data_provide_hint() -> None:
    gui = DummyGUI()

    commands_handler_gui.on_hint(gui)

    gui.game_data.provide_hint.assert_called_once()


def test_on_draw_gui_updates_preview_and_players_view() -> None:
    gui = DummyGUI()
    with patch.object(commands_handler_gui.utils, "tile_image_path", return_value="/tmp/CFFF.png"):
        commands_handler_gui.on_draw_gui(gui)

    gui.tile_preview.set_filename.assert_called_once_with("/tmp/CFFF.png")
    gui.update_preview_rotation.assert_called_once()
    assert not gui.players_view.refresh.called


def test_on_draw_gui_clears_preview_when_no_tile() -> None:
    gui = DummyGUI()
    gui.game_data.draw_tile.return_value = None

    commands_handler_gui.on_draw_gui(gui)

    gui.tile_preview.set_filename.assert_called_once_with("")
    assert gui.players_view.refresh.called
    gui.update_preview_rotation.assert_not_called()


def test_on_rotate_gui_rotates_tile_and_refreshes_preview() -> None:
    gui = DummyGUI()

    commands_handler_gui.on_rotate_gui(gui)

    gui.game_data.rotate_current_tile.assert_called_once()
    gui.tile_preview.update_rotation.assert_called_once()
    gui.update_preview_rotation.assert_called_once()


def test_on_end_turn_gui_plays_move_and_refreshes_players_view() -> None:
    gui = DummyGUI()

    commands_handler_gui.on_end_turn_gui(gui)

    gui.game_data.play_move_gui.assert_called_once()
    gui.players_view.refresh.assert_called_once()
