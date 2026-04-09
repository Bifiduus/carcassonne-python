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


def test_on_new_calls_start_and_shuffle() -> None:
    game = Mock()

    commands_handler_gui.on_new(game)

    game.start_new_game.assert_called_once()
    game.shuffle_deck.assert_called_once()


def test_on_new_gui_resets_pause_refreshes_and_clears_preview() -> None:
    gui = DummyGUI()
    gui.set_paused = Mock()
    gui.game_data.new_game = Mock()

    commands_handler_gui.on_new_gui(gui)

    gui.set_paused.assert_called_once_with(False)
    gui.game_data.new_game.assert_called_once_with(None, None)
    gui.players_view.refresh.assert_called_once()
    gui.tile_preview.set_filename.assert_called_once_with("")


def test_on_config_prints_configuration_and_switches_to_menu(capsys) -> None:
    gui = DummyGUI()
    gui.window = SimpleNamespace(stack=SimpleNamespace(set_visible_child_name=Mock()))
    gui.game_data.game_configuration = Mock(return_value={"river": True, "seed": 42})

    commands_handler_gui.on_config(gui)

    captured = capsys.readouterr().out
    assert "river" in captured
    assert "seed" in captured
    gui.window.stack.set_visible_child_name.assert_called_once_with("singleplayer_menu")


def test_on_quit_delegates_to_quit_method() -> None:
    app = Mock()

    commands_handler_gui.on_quit(app)

    app.quit.assert_called_once()


def test_on_info_shows_application_information() -> None:
    gui = DummyGUI()
    gui.info_message = SimpleNamespace(show_info=Mock())

    commands_handler_gui.on_info(gui)

    gui.info_message.show_info.assert_called_once()
    message = gui.info_message.show_info.call_args.args[0]
    assert "Carcassonne Python" in message
    assert "Version:" in message


def test_on_load_success_refreshes_gui_and_shows_messages() -> None:
    gui = DummyGUI()
    gui.window = SimpleNamespace(
        window=Mock(),
        stack=SimpleNamespace(set_visible_child_name=Mock()),
    )
    gui.info_message = SimpleNamespace(show_info=Mock())
    gui.error_message = SimpleNamespace(show_error=Mock())
    gui.board_view = SimpleNamespace(refresh=Mock())
    gui.players_view = SimpleNamespace(refresh=Mock())
    gui.set_paused = Mock()
    gui.game_data.reset = Mock()
    gui.game_data.game_configuration = Mock(
        side_effect=[{"river": False}, {"river": True}]
    )
    gui.game_data.game = SimpleNamespace(
        load_game_from_file=Mock(return_value=0),
        river_manager=SimpleNamespace(reset=Mock(), initialize_river=Mock()),
        get_board_data=Mock(return_value=[{"id": 0}]),
    )

    dialog = Mock()
    dialog.open_finish.return_value = SimpleNamespace(get_path=Mock(return_value="/tmp/save.txt"))

    def fake_open(_window, _cancellable, callback):
        callback(dialog, object())

    dialog.open = Mock(side_effect=fake_open)

    with patch.object(
        commands_handler_gui.Gtk,
        "FileDialog",
        return_value=dialog,
        create=True,
    ):
        commands_handler_gui.on_load(gui)

    gui.window.window.present.assert_called_once()
    gui.game_data.game.river_manager.reset.assert_called_once()
    gui.game_data.game.river_manager.initialize_river.assert_called_once()
    gui.game_data.reset.assert_called_once()
    assert gui.players_view.refresh.call_count >= 1
    assert gui.board_view.refresh.call_count >= 1
    gui.tile_preview.set_filename.assert_called_with("")
    gui.set_paused.assert_called_once_with(False)
    gui.window.stack.set_visible_child_name.assert_called_once_with("game")
    assert gui.info_message.show_info.call_count >= 1
    gui.error_message.show_error.assert_not_called()


def test_on_load_success_with_river_disabled_shows_disable_info() -> None:
    gui = DummyGUI()
    gui.window = SimpleNamespace(
        window=Mock(),
        stack=SimpleNamespace(set_visible_child_name=Mock()),
    )
    gui.info_message = SimpleNamespace(show_info=Mock())
    gui.game_data.reset = Mock()
    gui.game_data.game_configuration = Mock(
        side_effect=[{"river": True}, {"river": False}]
    )
    gui.game_data.game = SimpleNamespace(
        load_game_from_file=Mock(return_value=0),
        river_manager=SimpleNamespace(reset=Mock(), initialize_river=Mock()),
        get_board_data=Mock(return_value=[]),
    )

    dialog = Mock()
    dialog.open_finish.return_value = SimpleNamespace(get_path=Mock(return_value="/tmp/save.txt"))
    dialog.open = Mock(side_effect=lambda _w, _c, cb: cb(dialog, object()))

    with patch.object(
        commands_handler_gui.Gtk,
        "FileDialog",
        return_value=dialog,
        create=True,
    ):
        commands_handler_gui.on_load(gui)

    assert gui.info_message.show_info.call_count >= 1
    gui.game_data.game.river_manager.initialize_river.assert_not_called()


def test_on_load_failure_shows_error_message() -> None:
    gui = DummyGUI()
    gui.window = SimpleNamespace(window=Mock())
    gui.info_message = SimpleNamespace(show_info=Mock())
    gui.error_message = SimpleNamespace(show_error=Mock())
    gui.game_data.game_configuration = Mock(return_value={"river": False})
    gui.game_data.game = SimpleNamespace(load_game_from_file=Mock(return_value=1))

    dialog = Mock()
    dialog.open_finish.return_value = SimpleNamespace(get_path=Mock(return_value="/tmp/save.txt"))
    dialog.open = Mock(side_effect=lambda _w, _c, cb: cb(dialog, object()))

    with patch.object(
        commands_handler_gui.Gtk,
        "FileDialog",
        return_value=dialog,
        create=True,
    ):
        commands_handler_gui.on_load(gui)

    gui.error_message.show_error.assert_called_once()
    gui.info_message.show_info.assert_not_called()


def test_on_load_cancellation_is_silent() -> None:
    gui = DummyGUI()
    gui.window = SimpleNamespace(window=Mock())
    gui.error_message = SimpleNamespace(show_error=Mock())

    dialog = Mock()
    dialog.open_finish.side_effect = Exception("Operation was cancelled")
    dialog.open = Mock(side_effect=lambda _w, _c, cb: cb(dialog, object()))

    with patch.object(
        commands_handler_gui.Gtk,
        "FileDialog",
        return_value=dialog,
        create=True,
    ):
        commands_handler_gui.on_load(gui)

    gui.error_message.show_error.assert_not_called()


def test_on_load_exception_shows_error_message() -> None:
    gui = DummyGUI()
    gui.window = SimpleNamespace(window=Mock())
    gui.error_message = SimpleNamespace(show_error=Mock())

    dialog = Mock()
    dialog.open_finish.side_effect = Exception("boom")
    dialog.open = Mock(side_effect=lambda _w, _c, cb: cb(dialog, object()))

    with patch.object(
        commands_handler_gui.Gtk,
        "FileDialog",
        return_value=dialog,
        create=True,
    ):
        commands_handler_gui.on_load(gui)

    gui.error_message.show_error.assert_called_once()


def test_on_save_success_shows_info_message() -> None:
    gui = DummyGUI()
    gui.window = SimpleNamespace(window=Mock())
    gui.info_message = SimpleNamespace(show_info=Mock())
    gui.error_message = SimpleNamespace(show_error=Mock())
    gui.game_data.game = SimpleNamespace(save_game_to_file=Mock(return_value=0))

    dialog = Mock()
    dialog.save_finish.return_value = SimpleNamespace(get_path=Mock(return_value="/tmp/save.txt"))
    dialog.save = Mock(side_effect=lambda _w, _c, cb: cb(dialog, object()))

    with patch.object(
        commands_handler_gui.Gtk,
        "FileDialog",
        return_value=dialog,
        create=True,
    ):
        commands_handler_gui.on_save(gui)

    gui.info_message.show_info.assert_called_once()
    gui.error_message.show_error.assert_not_called()


def test_on_save_failure_and_exception_paths() -> None:
    gui = DummyGUI()
    gui.window = SimpleNamespace(window=Mock())
    gui.info_message = SimpleNamespace(show_info=Mock())
    gui.error_message = SimpleNamespace(show_error=Mock())
    gui.game_data.game = SimpleNamespace(save_game_to_file=Mock(return_value=1))

    dialog = Mock()
    dialog.save_finish.return_value = SimpleNamespace(get_path=Mock(return_value="/tmp/save.txt"))
    dialog.save = Mock(side_effect=lambda _w, _c, cb: cb(dialog, object()))

    with patch.object(
        commands_handler_gui.Gtk,
        "FileDialog",
        return_value=dialog,
        create=True,
    ):
        commands_handler_gui.on_save(gui)

    assert gui.error_message.show_error.call_count == 1

    dialog.save_finish.side_effect = Exception("boom")
    with patch.object(
        commands_handler_gui.Gtk,
        "FileDialog",
        return_value=dialog,
        create=True,
    ):
        commands_handler_gui.on_save(gui)

    assert gui.error_message.show_error.call_count == 2


def test_on_save_cancellation_is_silent() -> None:
    gui = DummyGUI()
    gui.window = SimpleNamespace(window=Mock())
    gui.error_message = SimpleNamespace(show_error=Mock())
    gui.game_data.game = SimpleNamespace(save_game_to_file=Mock(return_value=0))

    dialog = Mock()
    dialog.save_finish.side_effect = Exception("cancel")
    dialog.save = Mock(side_effect=lambda _w, _c, cb: cb(dialog, object()))

    with patch.object(
        commands_handler_gui.Gtk,
        "FileDialog",
        return_value=dialog,
        create=True,
    ):
        commands_handler_gui.on_save(gui)

    gui.error_message.show_error.assert_not_called()


def test_on_hint_delegates_to_game_data_provide_hint() -> None:
    gui = DummyGUI()

    commands_handler_gui.on_hint(gui)

    gui.game_data.provide_hint.assert_called_once()


def test_on_pause_delegates_to_gui_toggle_pause() -> None:
    gui = DummyGUI()
    gui.toggle_pause = Mock()

    commands_handler_gui.on_pause(gui)

    gui.toggle_pause.assert_called_once()


def test_on_pause_without_gui_prints_message(capsys) -> None:
    commands_handler_gui.on_pause(None)

    assert "Pause" in capsys.readouterr().out


def test_on_undo_delegates_to_game_service() -> None:
    game = Mock()

    commands_handler_gui.on_undo(game)

    game.undo.assert_called_once()


def test_on_redo_delegates_to_game_service() -> None:
    game = Mock()

    commands_handler_gui.on_redo(game)

    game.redo.assert_called_once()


def test_on_hint_is_ignored_while_game_is_paused() -> None:
    gui = DummyGUI()
    gui.is_paused = True

    commands_handler_gui.on_hint(gui)

    gui.game_data.provide_hint.assert_not_called()


def test_on_hint_shows_error_if_no_tile_in_hand() -> None:
    gui = DummyGUI()
    gui.error_message = SimpleNamespace(show_error=Mock())
    gui.game_data.game = SimpleNamespace(
        game_data=SimpleNamespace(current_hand=None)
    )

    commands_handler_gui.on_hint(gui)

    gui.error_message.show_error.assert_called_once()
    gui.game_data.provide_hint.assert_not_called()


def test_on_undo_gui_is_ignored_when_paused() -> None:
    gui = DummyGUI()
    gui.is_paused = True
    gui.game_data.undo = Mock()

    commands_handler_gui.on_undo_gui(gui)

    gui.game_data.undo.assert_not_called()


def test_on_redo_gui_is_ignored_when_paused() -> None:
    gui = DummyGUI()
    gui.is_paused = True
    gui.game_data.redo = Mock()

    commands_handler_gui.on_redo_gui(gui)

    gui.game_data.redo.assert_not_called()


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


def test_on_draw_gui_is_ignored_when_paused() -> None:
    gui = DummyGUI()
    gui.is_paused = True

    commands_handler_gui.on_draw_gui(gui)

    gui.game_data.draw_tile.assert_not_called()


def test_on_draw_gui_shows_already_have_tile_error() -> None:
    gui = DummyGUI()
    gui.error_message = SimpleNamespace(show_error=Mock())
    gui.game_data.draw_tile.return_value = None
    gui.game_data.game = SimpleNamespace(
        game_data=SimpleNamespace(
            no_playable_tiles_remaining=False,
            current_hand="CFFF",
            deck=SimpleNamespace(is_empty=Mock(return_value=False)),
        )
    )

    commands_handler_gui.on_draw_gui(gui)

    gui.error_message.show_error.assert_called_once()
    assert gui.tile_preview.set_filename.called


def test_on_draw_gui_shows_empty_deck_error() -> None:
    gui = DummyGUI()
    gui.error_message = SimpleNamespace(show_error=Mock())
    gui.game_data.draw_tile.return_value = None
    gui.game_data.game = SimpleNamespace(
        game_data=SimpleNamespace(
            no_playable_tiles_remaining=False,
            current_hand=None,
            deck=SimpleNamespace(is_empty=Mock(return_value=True)),
        )
    )

    commands_handler_gui.on_draw_gui(gui)

    gui.error_message.show_error.assert_called_once()
    assert gui.players_view.refresh.called


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


def test_on_rotate_gui_shows_error_when_no_tile_in_hand() -> None:
    gui = DummyGUI()
    gui.error_message = SimpleNamespace(show_error=Mock())
    gui.game_data.game = SimpleNamespace(
        game_data=SimpleNamespace(current_hand=None)
    )

    commands_handler_gui.on_rotate_gui(gui)

    gui.error_message.show_error.assert_called_once()
    gui.game_data.rotate_current_tile.assert_not_called()


def test_on_rotate_gui_is_ignored_when_paused() -> None:
    gui = DummyGUI()
    gui.is_paused = True

    commands_handler_gui.on_rotate_gui(gui)

    gui.game_data.rotate_current_tile.assert_not_called()


def test_on_end_turn_gui_plays_move_and_refreshes_players_view() -> None:
    gui = DummyGUI()

    commands_handler_gui.on_end_turn_gui(gui)

    gui.game_data.play_move_gui.assert_called_once()
    gui.players_view.refresh.assert_called_once()


def test_on_end_turn_gui_shows_error_when_no_placed_tile() -> None:
    gui = DummyGUI()
    gui.error_message = SimpleNamespace(show_error=Mock())
    gui.game_data.current_tile = None

    commands_handler_gui.on_end_turn_gui(gui)

    gui.error_message.show_error.assert_called_once()
    gui.game_data.play_move_gui.assert_not_called()


def test_on_end_turn_gui_shows_error_when_no_tile_in_hand() -> None:
    gui = DummyGUI()
    gui.error_message = SimpleNamespace(show_error=Mock())
    gui.game_data.current_tile = object()
    gui.game_data.game = SimpleNamespace(game_data=SimpleNamespace(current_hand=None))

    commands_handler_gui.on_end_turn_gui(gui)

    gui.error_message.show_error.assert_called_once()
    gui.game_data.play_move_gui.assert_not_called()


def test_on_end_turn_gui_is_ignored_when_paused() -> None:
    gui = DummyGUI()
    gui.is_paused = True

    commands_handler_gui.on_end_turn_gui(gui)

    gui.game_data.play_move_gui.assert_not_called()


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


def test_on_undo_gui_calls_undo_when_history_exists() -> None:
    gui = DummyGUI()
    gui.error_message = SimpleNamespace(show_error=Mock())
    gui.game_data.game = SimpleNamespace(
        game_data=SimpleNamespace(history=SimpleNamespace(past_moves=[1]))
    )
    gui.game_data.undo = Mock()

    commands_handler_gui.on_undo_gui(gui)

    gui.error_message.show_error.assert_not_called()
    gui.game_data.undo.assert_called_once()


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


def test_on_redo_gui_shows_error_when_no_future_moves() -> None:
    gui = DummyGUI()
    gui.error_message = SimpleNamespace(show_error=Mock())
    gui.game_data.game = SimpleNamespace(
        game_data=SimpleNamespace(history=SimpleNamespace(future_moves=[]))
    )
    gui.game_data.redo = Mock()

    commands_handler_gui.on_redo_gui(gui)

    gui.error_message.show_error.assert_called_once()
    gui.game_data.redo.assert_not_called()
