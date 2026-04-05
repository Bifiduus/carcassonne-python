from contextlib import ExitStack
from types import SimpleNamespace
from unittest.mock import Mock, patch

import carcassonne.presentation.cli.cli as cli_module


class DummyPlayer:
    def __init__(self, player_id: int, username: str = "P", score: int = 0, is_ai: bool = False):
        self.player_id = player_id
        self.username = username
        self.score = score
        self.ai = is_ai

    def get_id(self) -> int:
        return self.player_id

    def get_username(self) -> str:
        return self.username

    def get_score_int(self) -> int:
        return self.score

    def is_ai_player(self) -> bool:
        return self.ai


def build_cli():
    current_player = DummyPlayer(1)
    game = Mock()
    game.get_game_configuration.return_value = {}
    game.get_current_player.return_value = current_player
    game.tick_blitz.return_value = False
    game.get_timeout_message.return_value = ""
    game.end_game.return_value = False
    game.get_players_order.return_value = [1, 2]
    game.game_data = SimpleNamespace(
        players={
            1: DummyPlayer(1, "Alice", 12),
            2: DummyPlayer(2, "Bob", 8),
        }
    )
    server = Mock()
    client = Mock()
    with (
        patch.object(cli_module.readline, "set_completer"),
        patch.object(cli_module.readline, "parse_and_bind"),
        patch.object(cli_module.readline, "read_history_file"),
    ):
        return cli_module.GameCLI(game, server, client), game, server, client


def test_completer_and_cli_helpers_cover_basic_cases() -> None:
    with patch.object(cli_module.readline, "get_line_buffer", return_value="sh"):
        assert cli_module.completer("sh", 0) == "shuffle"
    with patch.object(cli_module.readline, "get_line_buffer", return_value="zzz"):
        assert cli_module.completer("zzz", 0) is None

    cli, game, _, _ = build_cli()
    assert cli._is_turn_bound_command("draw") is True
    assert cli._is_turn_bound_command("play CFFF/0N0") is True
    assert cli._is_turn_bound_command("help") is False
    assert cli._local_player_can_act() is True

    game.get_current_player.return_value = DummyPlayer(2)
    assert cli._local_player_can_act() is False


def test_cli_handle_command_dispatches_to_handlers_and_reports_unknown(capsys) -> None:
    cli, game, server, client = build_cli()
    with ExitStack() as stack:
        add_history = stack.enter_context(
            patch.object(cli_module.readline, "add_history")
        )
        new_game = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "new_game")
        )
        help_cmd = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "help")
        )
        quit_cmd = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "quit")
        )
        load_cmd = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "load")
        )
        save_cmd = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "save")
        )
        shuffle_cmd = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "shuffle")
        )
        draw_cmd = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "draw")
        )
        hint_cmd = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "hint")
        )
        undo_cmd = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "undo")
        )
        redo_cmd = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "redo")
        )
        show_hand = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "show_hand")
        )
        show_time = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "show_time")
        )
        show_score = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "show_score")
        )
        show_history = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "show_history")
        )
        show_configuration = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "show_configuration")
        )
        set_parameter = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "set_parameter")
        )
        players = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "players")
        )
        play = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "play")
        )
        show_board = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "show_board")
        )
        show_server_list = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "show_server_list")
        )
        server_start = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "server_start")
        )
        stop_server = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "stop_server")
        )
        join = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "join")
        )
        ping = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "ping")
        )
        server_status = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "server_status")
        )
        scoreboard = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "scoreboard")
        )
        accept = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "accept")
        )
        decline = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "decline")
        )
        cancel = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "cancel")
        )
        back = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "back")
        )
        away = stack.enter_context(
            patch.object(cli_module.commands_handler_cli, "away")
        )

        cli.handle_command("new players")
        cli.handle_command("help")
        cli.handle_command("quit")
        cli.handle_command("load save.txt")
        cli.handle_command("save save.txt")
        cli.handle_command("shuffle")
        cli.handle_command("draw")
        cli.handle_command("hint")
        cli.handle_command("undo")
        cli.handle_command("redo")
        cli.handle_command("show hand")
        cli.handle_command("show time 2")
        cli.handle_command("show score")
        cli.handle_command("show history")
        cli.handle_command("show configuration")
        cli.handle_command("set ai_mode=random")
        cli.handle_command("players 2")
        cli.handle_command("play CFFF/0N0")
        cli.handle_command("board")
        cli.handle_command("server list")
        cli.handle_command("server start 4242")
        cli.handle_command("server stop")
        cli.handle_command("join 127.0.0.1:4242")
        cli.handle_command("join 127.0.0.1")
        cli.handle_command("ping")
        cli.handle_command("server status")
        cli.handle_command("scoreboard")
        cli.handle_command("accept")
        cli.handle_command("decline")
        cli.handle_command("cancel")
        cli.handle_command("back")
        cli.handle_command("away")
        cli.handle_command("mystery")

    new_game.assert_called_once()
    help_cmd.assert_called_once()
    quit_cmd.assert_called_once_with(cli, server, client)
    load_cmd.assert_called_once()
    save_cmd.assert_called_once()
    shuffle_cmd.assert_called_once()
    draw_cmd.assert_called_once()
    hint_cmd.assert_called_once()
    undo_cmd.assert_called_once_with(cli, 1, client)
    redo_cmd.assert_called_once_with(cli, 1, client)
    show_hand.assert_called_once()
    show_time.assert_called_once_with(cli, "2")
    show_score.assert_called_once()
    show_history.assert_called_once()
    show_configuration.assert_called_once()
    set_parameter.assert_called_once_with(cli, "ai_mode", "random", client)
    players.assert_called_once_with(cli, client, "players 2")
    play.assert_called_once()
    show_board.assert_called_once()
    show_server_list.assert_called_once()
    server_start.assert_called_once()
    stop_server.assert_called_once()
    assert join.call_count == 2
    ping.assert_called_once()
    server_status.assert_called_once()
    scoreboard.assert_called_once()
    accept.assert_called_once()
    decline.assert_called_once()
    cancel.assert_called_once()
    back.assert_called_once()
    away.assert_called_once()
    assert add_history.call_count == 33
    assert "Unknown command. Type 'help' to see the list of commands." in capsys.readouterr().out


def test_cli_rejects_turn_bound_commands_when_local_player_cannot_act(capsys) -> None:
    cli, game, _, _ = build_cli()
    cli.local_player_id = 7
    game.get_current_player.return_value = DummyPlayer(1)

    with patch.object(cli_module.readline, "add_history") as add_history:
        cli.handle_command("draw")

    output = capsys.readouterr().out
    assert "Command rejected: it is not your turn" in output
    add_history.assert_not_called()


def test_tick_once_and_on_game_over_cover_timeout_ai_and_final_scores(capsys) -> None:
    cli, game, _, _ = build_cli()
    game.get_timeout_message.return_value = "Timeout!"
    game.get_current_player.return_value = DummyPlayer(2, is_ai=True)
    cli.local_player_id = 1

    cli._tick_once()

    assert game.play_ai_turn.called
    assert game.get_board.called
    output = capsys.readouterr().out
    assert "Timeout!" in output

    cli.running = True
    game.get_board.reset_mock()
    cli._on_game_over()
    output = capsys.readouterr().out
    assert "=== Game finished! Final scores ===" in output
    assert "1. Alice: 12 points" in output
    assert "2. Bob: 8 points" in output
    assert cli.running is False
    game.get_board.assert_called()


def test_run_executes_main_loop_and_writes_history() -> None:
    cli, _, _, _ = build_cli()

    def stop_after_tick():
        cli.running = False

    with (
        patch.object(cli, "_start_input_loop"),
        patch.object(cli, "_tick_once", side_effect=stop_after_tick),
        patch.object(cli_module.time, "monotonic", side_effect=[0.0, 0.2]),
        patch.object(cli_module.time, "sleep"),
        patch.object(cli_module.readline, "write_history_file") as write_history,
    ):
        cli.run()

    write_history.assert_called_once_with(".carcassonne_history")
