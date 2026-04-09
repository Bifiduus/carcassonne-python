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
        self.show_end_game_screen = Mock()


def test_on_hint_delegates_to_game_data_provide_hint() -> None:
    gui = DummyGUI()

    commands_handler_gui.on_hint(gui)

    gui.game_data.provide_hint.assert_called_once()


def test_on_pause_delegates_to_gui_toggle_pause() -> None:
    gui = DummyGUI()
    gui.toggle_pause = Mock()

    commands_handler_gui.on_pause(gui)

    gui.toggle_pause.assert_called_once()


def test_on_hint_is_ignored_while_game_is_paused() -> None:
    gui = DummyGUI()
    gui.is_paused = True

    commands_handler_gui.on_hint(gui)

    gui.game_data.provide_hint.assert_not_called()


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


def test_on_draw_gui_shows_end_game_screen_when_no_playable_tiles_remain() -> None:
    gui = DummyGUI()
    gui.error_message = SimpleNamespace(show_error=Mock())
    gui.game_data.draw_tile.return_value = None
    gui.game_data.game = SimpleNamespace(
        game_data=SimpleNamespace(
            no_playable_tiles_remaining=True,
            current_hand=None,
            deck=SimpleNamespace(is_empty=Mock(return_value=False)),
        )
    )

    commands_handler_gui.on_draw_gui(gui)

    gui.show_end_game_screen.assert_called_once()
    gui.error_message.show_error.assert_called_once()


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


def test_on_undo_gui_shows_error_when_no_past_moves() -> None:
    gui = DummyGUI()
    gui.error_message = SimpleNamespace(show_error=Mock())
    gui.game_data.game = SimpleNamespace(
        game_data=SimpleNamespace(history=SimpleNamespace(past_moves=[]))
    )
    gui.game_data.undo = Mock()

    commands_handler_gui.on_undo_gui(gui)

    gui.error_message.show_error.assert_called_once()
    gui.game_data.undo.assert_not_called()


def test_on_redo_gui_uses_history_future_moves() -> None:
    gui = DummyGUI()
    gui.error_message = SimpleNamespace(show_error=Mock())
    gui.game_data.game = SimpleNamespace(
        game_data=SimpleNamespace(history=SimpleNamespace(future_moves=[1]))
    )
    gui.game_data.redo = Mock()

    commands_handler_gui.on_redo_gui(gui)

    gui.error_message.show_error.assert_not_called()
    gui.game_data.redo.assert_called_once()
