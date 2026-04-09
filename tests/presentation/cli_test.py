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
    game.get_winner.return_value = DummyPlayer(1, "Alice", 12)
    game.get_winners.return_value = [DummyPlayer(1, "Alice", 12)]
    game.is_draw.return_value = False
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


def test_cli_init_ignores_missing_history_file() -> None:
    game = Mock()
    game.get_game_configuration.return_value = {}
    game.get_current_player.return_value = DummyPlayer(1)
    server = Mock()
    client = Mock()

    with (
        patch.object(cli_module.readline, "set_completer"),
        patch.object(cli_module.readline, "parse_and_bind"),
        patch.object(
            cli_module.readline,
            "read_history_file",
            side_effect=FileNotFoundError,
        ),
    ):
        cli = cli_module.GameCLI(game, server, client)

    assert cli.local_player_id == 1


def test_completer_and_cli_helpers_cover_basic_cases() -> None:
    cli_module._LAST_AMBIGUOUS_QUERY = ""
    with patch.object(
        cli_module.readline,
        "get_line_buffer",
        return_value="shuffle",
    ):
        assert cli_module.completer("shuffle", 0) == "shuffle"
    with patch.object(cli_module.readline, "get_line_buffer", return_value="zzz"):
        assert cli_module.completer("zzz", 0) is None

    cli, game, _, _ = build_cli()
    assert cli._is_turn_bound_command("draw") is True
    assert cli._is_turn_bound_command("play CFFF/0N0") is True
    assert cli._is_turn_bound_command("help") is False
    assert cli._local_player_can_act() is True

    game.get_current_player.return_value = DummyPlayer(2)
    assert cli._local_player_can_act() is False


def test_completer_ambiguous_input_beeps_then_lists_matches(capsys) -> None:
    cli_module._LAST_AMBIGUOUS_QUERY = ""

    with patch.object(cli_module.readline, "get_line_buffer", return_value="h"):
        assert cli_module.completer("h", 0) == ""
    first_tab = capsys.readouterr().out
    assert "\a" in first_tab

    with patch.object(cli_module.readline, "get_line_buffer", return_value="h"):
        assert cli_module.completer("h", 0) == ""
    second_tab = capsys.readouterr().out
    assert "help" in second_tab
    assert "hint" in second_tab

    with patch.object(cli_module.readline, "get_line_buffer", return_value="h"):
        assert cli_module.completer("h", 0) == ""
    third_tab = capsys.readouterr().out
    assert "\a" not in third_tab
    assert "help" in third_tab
    assert "hint" in third_tab


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
    help_cmd.assert_called_once_with(cli, None)
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
    unknown_output = capsys.readouterr().out
    assert "Unknown command" in unknown_output
    assert "help" in unknown_output


def test_cli_handle_command_supports_help_with_command_name() -> None:
    cli, _, _, _ = build_cli()

    with (
        patch.object(cli_module.readline, "add_history"),
        patch.object(cli_module.commands_handler_cli, "help") as help_cmd,
    ):
        cli.handle_command("help undo")

    help_cmd.assert_called_once_with(cli, "undo")


def test_cli_handle_command_parses_undo_redo_counts_and_reports_usage(
    capsys,
) -> None:
    cli, _, _, client = build_cli()

    with (
        patch.object(cli_module.readline, "add_history"),
        patch.object(cli_module.commands_handler_cli, "undo") as undo_cmd,
        patch.object(cli_module.commands_handler_cli, "redo") as redo_cmd,
    ):
        cli.handle_command("undo 3")
        cli.handle_command("redo 2")
        cli.handle_command("undo nope")
        cli.handle_command("redo 0")

    undo_cmd.assert_called_once_with(cli, 3, client)
    redo_cmd.assert_called_once_with(cli, 2, client)
    output = capsys.readouterr().out
    assert "Usage:" in output
    assert "undo" in output
    assert "redo" in output


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
    assert game.get_printed_board.called
    output = capsys.readouterr().out
    assert "Timeout!" in output

    cli.running = True
    game.get_printed_board.reset_mock()
    cli._on_game_over()
    output = capsys.readouterr().out
    assert "=== Game finished! Final scores ===" in output
    assert "Winner: Alice" in output
    assert "1. Alice: 12 points" in output
    assert "2. Bob: 8 points" in output
    assert cli.running is False
    game.get_printed_board.assert_called()


def test_on_game_over_prints_draw_when_scores_are_tied(capsys) -> None:
    cli, game, _, _ = build_cli()
    game.get_winner.return_value = None
    game.get_winners.return_value = [
        DummyPlayer(1, "Alice", 12),
        DummyPlayer(2, "Bob", 12),
    ]
    game.game_data = SimpleNamespace(
        players={
            1: DummyPlayer(1, "Alice", 12),
            2: DummyPlayer(2, "Bob", 12),
        }
    )

    cli._on_game_over()

    output = capsys.readouterr().out
    assert "Draw: Alice, Bob" in output


def test_run_executes_main_loop_and_writes_history() -> None:
    cli, _, _, _ = build_cli()

    with (
        patch.object(cli, "_tick_once"),
        patch.object(cli, "_start_tick_loop"),
        patch.object(cli, "_install_wakeup_signal_handler"),
        patch.object(cli, "_restore_wakeup_signal_handler"),
        patch("builtins.input", side_effect=EOFError),
        patch.object(cli_module.readline, "write_history_file") as write_history,
    ):
        cli.run()

    write_history.assert_called_once_with(".carcassonne_history")


def test_run_handles_keyboard_interrupt_and_joins_tick_thread(
    capsys,
) -> None:
    cli, _, _, _ = build_cli()
    cli._tick_thread = Mock()
    cli._tick_thread.join = Mock()

    with (
        patch.object(cli, "_tick_once"),
        patch.object(cli, "_start_tick_loop"),
        patch.object(cli, "_install_wakeup_signal_handler"),
        patch.object(cli, "_restore_wakeup_signal_handler"),
        patch("builtins.input", side_effect=KeyboardInterrupt),
        patch.object(cli_module.readline, "write_history_file") as write_history,
    ):
        cli.run()

    assert "Game over" in capsys.readouterr().out
    cli._tick_thread.join.assert_called_once_with(timeout=0.2)
    write_history.assert_called_once_with(".carcassonne_history")


def test_start_tick_loop_skips_when_thread_is_already_running() -> None:
    cli, _, _, _ = build_cli()
    cli._tick_thread = Mock()
    cli._tick_thread.is_alive.return_value = True

    with patch.object(cli_module.threading, "Thread") as thread_ctor:
        cli._start_tick_loop()

    thread_ctor.assert_not_called()


def test_tick_loop_calls_tick_once_until_stopped() -> None:
    cli, game, _, _ = build_cli()
    tick_once = Mock(side_effect=lambda: setattr(cli, "running", False))

    with (
        patch.object(cli, "_tick_once", tick_once),
        patch.object(cli_module.time, "monotonic", side_effect=[0.0, 0.2]),
        patch.object(cli_module.time, "sleep"),
    ):
        cli._tick_loop()

    tick_once.assert_called_once_with()


def test_wakeup_signal_handler_install_restore_and_raise() -> None:
    cli, _, _, _ = build_cli()
    cli._wakeup_signal = 10

    with (
        patch.object(cli_module.signal, "getsignal", return_value="old"),
        patch.object(cli_module.signal, "signal") as signal_mock,
    ):
        cli._install_wakeup_signal_handler()
        cli._restore_wakeup_signal_handler()

    assert cli._previous_wakeup_handler is None
    assert signal_mock.call_count == 2

    try:
        cli._handle_game_finished_signal(10, None)
        assert False
    except cli_module.GameFinishedInterrupt:
        pass


def test_wake_input_prompt_only_signals_from_background_thread() -> None:
    cli, _, _, _ = build_cli()
    cli._wakeup_signal = 10

    with (
        patch.object(cli_module.threading, "current_thread", return_value="main"),
        patch.object(cli_module.threading, "main_thread", return_value="main"),
        patch.object(cli_module.os, "kill") as kill_mock,
    ):
        cli._wake_input_prompt()

    kill_mock.assert_not_called()

    with (
        patch.object(cli_module.threading, "current_thread", return_value="worker"),
        patch.object(cli_module.threading, "main_thread", return_value="main"),
        patch.object(cli_module.os, "kill") as kill_mock,
        patch.object(cli_module.os, "getpid", return_value=123),
    ):
        cli._wake_input_prompt()

    kill_mock.assert_called_once_with(123, 10)


def test_on_game_over_ignores_repeated_calls() -> None:
    cli, game, _, _ = build_cli()
    cli.running = False

    cli._on_game_over()

    game.get_board.assert_not_called()


def test_handle_command_reports_usage_for_invalid_set_syntax(capsys) -> None:
    cli, _, _, _ = build_cli()

    with (
        patch.object(cli_module.readline, "add_history"),
        patch.object(cli_module.commands_handler_cli, "set_parameter") as setter,
    ):
        cli.handle_command("set blitz")

    setter.assert_not_called()
    invalid_set_output = capsys.readouterr().out
    assert "Usage:" in invalid_set_output
    assert "set" in invalid_set_output
