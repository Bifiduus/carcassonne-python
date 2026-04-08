from carcassonne.presentation.gui.game_data_gui import GameDataGui
from carcassonne.presentation.gui.tiles_view import TilesView
import pytest
from types import SimpleNamespace
from unittest.mock import Mock, patch

pytest.importorskip("gi")


class DummyTilesInfo:
    direction_dict = {"N": 0, "E": 1, "S": 2, "W": 3}


class DummyGame:
    def __init__(self, hint_move, adjacent_position=(1, 2)) -> None:
        self.provide_hint = Mock(return_value=hint_move)
        self.get_adjacent_position = Mock(return_value=adjacent_position)
        self.get_board_data = Mock(
            return_value=[{"id": 0, "x": 0, "y": 0}]
        )
        self.game_data = SimpleNamespace(tiles_info=DummyTilesInfo())

        # Parse hint_move to create appropriate parse_move response
        if hint_move:
            parts = hint_move.split("/")
            tile_sides = parts[0] if parts else "CFFF"
            extra_info = parts[1] if len(parts) > 1 else "0N0"
            # Parse extra_info: first char(s) is target_id, next is target_side, last is rotation
            # Format: [target_id][target_side][rotation]
            # e.g., "5E1" -> target_id=5, target_side=E, rotation=1
            target_id = int(extra_info[0]) if extra_info[0].isdigit() else 0
            target_side = extra_info[1] if len(extra_info) > 1 else "N"
            rotation = int(extra_info[-1]) if extra_info[-1].isdigit() else 0
        else:
            tile_sides = "CFFF"
            target_id = 0
            target_side = "N"
            rotation = 0

        self.parse_move = Mock(return_value={
            "tile_sides": tile_sides,
            "rotation": rotation,
            "target_id": target_id,
            "target_side": target_side,
            "center": None,
            "meeple": ""
        })


def make_game_data_gui(game=None, client_service=None, server_service=None):
    """Factory for creating GameDataGui instances with mocks."""
    if game is None:
        game = DummyGame("CFFF/0N0")
    if client_service is None:
        client_service = Mock()
    if server_service is None:
        server_service = Mock()
    return GameDataGui(game, client_service, server_service)


def test_provide_hint_sets_hint_empty_positions_and_requests_redraw() -> None:
    game = DummyGame("CFFF/0N0")
    gui_data = GameDataGui(game, client_service=Mock(), server_service=Mock())
    gui_data.board_view = SimpleNamespace(queue_draw=Mock())

    hint_move = gui_data.provide_hint()

    assert hint_move == "CFFF/0N0"
    game.provide_hint.assert_called_once()
    assert game.get_adjacent_position.call_count == 4
    assert gui_data.hint_empty_positions == [(1, 2)]
    assert gui_data.hint_tile is None
    assert gui_data.hint_neighbor_id is None
    gui_data.board_view.queue_draw.assert_called_once()


def test_provide_hint_returns_empty_without_hint_tile() -> None:
    game = DummyGame("")
    gui_data = GameDataGui(game, client_service=Mock(), server_service=Mock())
    gui_data.board_view = SimpleNamespace(queue_draw=Mock())

    hint_move = gui_data.provide_hint()

    assert hint_move == ""
    assert game.provide_hint.called
    game.get_adjacent_position.assert_not_called()
    game.get_board_data.assert_not_called()
    assert gui_data.hint_tile is None
    assert gui_data.hint_neighbor_id is None
    assert gui_data.hint_empty_positions == []
    gui_data.board_view.queue_draw.assert_not_called()


def test_game_data_gui_initialization() -> None:
    game = Mock()
    client = Mock()
    server = Mock()

    gui_data = GameDataGui(game, client, server)

    assert gui_data.game is game
    assert gui_data.client is client
    assert gui_data.server is server
    assert gui_data.nb_tiles == 0
    assert gui_data.current_tile is None
    assert gui_data.current_orientation == 0
    assert gui_data.board_view is None
    assert gui_data.gui is None
    assert gui_data.is_dragging is False
    assert gui_data.hint_tile is None
    assert gui_data.hint_neighbor_id is None
    assert gui_data.hint_empty_positions == []


def test_game_configuration_returns_game_configuration() -> None:
    game = Mock()
    game.get_game_configuration.return_value = {"players_count": 2}
    gui_data = GameDataGui(game, Mock(), Mock())

    config = gui_data.game_configuration()

    assert config == {"players_count": 2}
    game.get_game_configuration.assert_called_once()


def test_pause_and_resume_delegate_to_game_service() -> None:
    game = Mock()
    gui_data = GameDataGui(game, Mock(), Mock())

    gui_data.pause_game()
    gui_data.resume_game()

    game.pause_game.assert_called_once_with()
    game.resume_game.assert_called_once_with()


def test_new_game_starts_new_game_and_resets_state() -> None:
    game = Mock()
    gui_data = GameDataGui(game, Mock(), Mock())
    # Set initial state with some data
    gui_data.hint_tile = {"dummy": "data"}
    gui_data.hint_neighbor_id = 5
    gui_data.hint_empty_positions = [(1, 0)]
    gui_data.nb_tiles = 5
    initial_current_tile = Mock()
    gui_data.current_tile = initial_current_tile
    gui_data.current_orientation = 2

    # Call new_game which should call reset()
    gui_data.new_game([1, 2, 3], 12345)

    # Verify game.start_new_game was called
    game.start_new_game.assert_called_once_with([1, 2, 3], 12345)
    # Verify reset() was called (state reset to initial values)
    # reset() clears all hint visual state
    assert gui_data.hint_tile is None
    assert gui_data.hint_neighbor_id is None
    assert gui_data.hint_empty_positions == []
    assert gui_data.current_tile is None
    assert gui_data.current_orientation == 0
    # nb_tiles is NOT reset by reset() method, it's managed separately
    # This is by design - it counts tiles drawn in the game


def test_play_move_gui_sets_error_and_shows_dialog_when_move_fails() -> None:
    game = Mock()
    game.play_move.return_value = False
    game.is_undo_history_empty.return_value = True
    game.get_current_player.return_value = SimpleNamespace(
        get_id=Mock(return_value=0),
        is_ai_player=Mock(return_value=False),
        get_meeples=Mock(return_value=0),
    )
    game.game_data = SimpleNamespace(
        current_hand="CFFF",
        players_order=[0],
        current_player_order_list=0,
        extract_tile_code=Mock(return_value="CFFF"),
    )

    gui_data = GameDataGui(game, Mock(), Mock())
    gui_data.current_tile = TilesView("CFFF", tile_id=1)
    gui_data.current_tile.move = "CFFF/0N0/N"
    gui_data.gui = SimpleNamespace(
        error_message=Mock(),
        show_end_game_screen=Mock(),
    )
    game.end_game.return_value = False

    gui_data.play_move_gui()

    assert gui_data.get_error() is not None
    assert "meeple" in gui_data.get_error().lower()
    gui_data.gui.error_message.show_error.assert_called_once_with(
        gui_data.get_error()
    )


def test_undo_calls_game_undo_and_refreshes_views() -> None:
    game = Mock()
    gui_data = GameDataGui(game, Mock(), Mock())
    gui_data.board_view = Mock()
    gui_data.gui = Mock()
    gui_data.gui.players_view = Mock()

    with patch("carcassonne.presentation.gui.game_data_gui.commands_handler_gui.on_undo"):
        gui_data.undo()

    gui_data.board_view.refresh.assert_called_once()
    gui_data.gui.players_view.refresh.assert_called_once()


def test_undo_without_board_view() -> None:
    game = Mock()
    gui_data = GameDataGui(game, Mock(), Mock())
    gui_data.board_view = None
    gui_data.gui = None

    with patch("carcassonne.presentation.gui.game_data_gui.commands_handler_gui.on_undo"):
        gui_data.undo()  # Should not raise


def test_redo_calls_game_redo_and_refreshes_views() -> None:
    game = Mock()
    gui_data = GameDataGui(game, Mock(), Mock())
    gui_data.board_view = Mock()
    gui_data.gui = Mock()
    gui_data.gui.players_view = Mock()

    with patch("carcassonne.presentation.gui.game_data_gui.commands_handler_gui.on_redo"):
        gui_data.redo()

    gui_data.board_view.refresh.assert_called_once()
    gui_data.gui.players_view.refresh.assert_called_once()


def test_redo_without_board_view() -> None:
    game = Mock()
    gui_data = GameDataGui(game, Mock(), Mock())
    gui_data.board_view = None
    gui_data.gui = None

    with patch("carcassonne.presentation.gui.game_data_gui.commands_handler_gui.on_redo"):
        gui_data.redo()  # Should not raise


def test_provide_hint_with_different_vertices_and_sides() -> None:
    game = DummyGame("CDFF/5E1", adjacent_position=(3, 4))
    gui_data = GameDataGui(game, Mock(), Mock())
    gui_data.board_view = Mock()

    hint_move = gui_data.provide_hint()

    assert hint_move == "CDFF/5E1"
    assert gui_data.hint_empty_positions == [(3, 4)]
    assert gui_data.hint_neighbor_id is None
    assert gui_data.hint_tile is None
