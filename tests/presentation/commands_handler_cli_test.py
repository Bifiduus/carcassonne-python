from types import SimpleNamespace
from unittest.mock import Mock

from carcassonne.presentation.cli import commands_handler_cli as handlers


class DummyPlayer:
    def __init__(
        self,
        player_id: int,
        username: str | None = None,
        score: int = 0,
        is_ai: bool = False,
    ) -> None:
        self.player_id = player_id
        self.username = username or f"Player {player_id}"
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


def build_local_context():
    player = DummyPlayer(1, username="Alice", score=12, is_ai=False)
    opponent = DummyPlayer(2, username="Bob", score=8, is_ai=False)
    history = SimpleNamespace(past_moves=[1], future_moves=[2])
    game = SimpleNamespace(
        start_new_game=Mock(),
        load_game_from_file=Mock(return_value=0),
        save_game_to_file=Mock(return_value=0),
        shuffle_deck=Mock(return_value=123),
        draw_tile=Mock(return_value="CFFF"),
        provide_hint=Mock(return_value="CFFF/12N2/SW"),
        undo=Mock(),
        redo=Mock(),
        get_game_configuration=Mock(return_value={"blitz": True, "ai_mode": "random"}),
        get_all_players_remaining_time_seconds=Mock(return_value=[(1, 65.0)]),
        get_player_remaining_time_seconds=Mock(return_value=42.0),
        get_history=Mock(return_value=["0:CFFF/0N0;", "1:FFFF/m/1E0;"]),
        set_game_configuration=Mock(),
        play_move=Mock(return_value=True),
        get_printed_board=Mock(return_value="BOARD"),
        is_undo_history_empty=Mock(return_value=False),
        clear_undo_history=Mock(),
        end_game=Mock(return_value=False),
        play_ai_turn=Mock(),
        get_current_player=Mock(return_value=player),
        get_players_order=Mock(return_value=[1, 2]),
        get_players_order=Mock(return_value=[1, 2]),
        game_data=SimpleNamespace(
            current_hand=None,
            shuffle_algo="fisher-yates",
            history=history,
            players={
                1: SimpleNamespace(get_score_int=lambda: 12),
                2: SimpleNamespace(get_score_int=lambda: 8),
            },
        ),
    )
    cli = SimpleNamespace(game=game, running=True)
    client = SimpleNamespace(
        connected_to_a_server=Mock(return_value=False),
        send_to_server=Mock(),
        list_available_servers=Mock(return_value={"127.0.0.1": 5000}),
        join_server=Mock(),
        ping=Mock(return_value="pong"),
    )
    server = SimpleNamespace(
        is_server_running=Mock(return_value=False),
        server_start=Mock(),
        server_stop=Mock(),
    )
    return cli, game, client, server


def test_local_command_handlers_cover_main_game_actions(capsys) -> None:
    cli, game, client, server = build_local_context()

    handlers.new_game(cli, "", client)
    handlers.help(cli)
    handlers.load(cli, "save1", client)
    game.load_game_from_file.return_value = -1
    handlers.load(cli, "save2", client)
    handlers.save(cli, "save3", client)
    handlers.shuffle(cli, client)

    game.draw_tile.return_value = None
    handlers.draw(cli, client)
    game.game_data.current_hand = "OLD"
    game.draw_tile.return_value = "NEW"
    handlers.draw(cli, client)
    game.game_data.current_hand = None
    game.draw_tile.return_value = "CFFF"
    handlers.draw(cli, client)

    game.game_data.current_hand = None
    handlers.show_hand(cli, client)
    game.game_data.current_hand = "FRFR"
    handlers.show_hand(cli, client)
    handlers.show_score(cli, client)
    handlers.show_history(cli, game, client)
    handlers.show_configuration(cli, game, client)
    handlers.set_parameter(cli, "ai_mode", "minimax", client)
    handlers.show_board(cli, game, client)
    handlers.show_server_list(cli, client)
    handlers.server_start(cli, "4242", server)
    handlers.stop_server(cli, server)
    handlers.join(cli, client)
    handlers.join(cli, client, "127.0.0.1", "4242")
    handlers.join(cli, client, "127.0.0.1")
    handlers.ping(cli, client)
    handlers.server_status(cli, client)
    handlers.players(cli, client, "players 2")
    handlers.scoreboard(cli, client)
    handlers.accept(cli, client)
    handlers.decline(cli, client)
    handlers.cancel(cli, client)
    handlers.back(cli, client)
    handlers.away(cli, client)

    output = capsys.readouterr().out
    assert "New game started." in output
    assert "Available commands:" in output
    assert "help [CMD]" in output
    assert "Game loaded from save1." in output
    assert "Failed to load the game from save2." in output
    assert "Game saved to save3." in output
    assert "Deck shuffled. Algorithm: fisher-yates. Seed: 123" in output
    assert "The deck is empty!" in output
    assert "You already have a tile in hand." in output
    assert "Tile drawn: CFFF" in output
    assert "No tile in hand." in output
    assert "Tile in hand: FRFR" in output
    assert "Player scores:" in output
    assert "Alice: 12 points" in output
    assert "Bob: 8 points" in output
    assert "Move history:" in output
    assert "Current game configuration:" in output
    assert "Parameter 'ai_mode' set to 'minimax'." in output
    assert "Available servers list:" in output
    assert "127.0.0.1:5000" in output
    client.send_to_server.assert_any_call("ping")

    game.start_new_game.assert_called_once_with()
    game.get_printed_board.assert_called()
    server.server_start.assert_called_once_with("4242")
    server.server_stop.assert_called_once_with()
    client.send_to_server.assert_any_call("server status")
    client.send_to_server.assert_any_call("players 2")
    client.send_to_server.assert_any_call("scoreboard")
    client.send_to_server.assert_any_call("accept")
    client.send_to_server.assert_any_call("decline")
    client.send_to_server.assert_any_call("cancel")
    client.send_to_server.assert_any_call("back")
    client.send_to_server.assert_any_call("away")
    client.join_server.assert_any_call()
    client.join_server.assert_any_call("127.0.0.1", 4242)
    client.join_server.assert_any_call("127.0.0.1")


def test_help_with_specific_command_displays_only_requested_help(capsys) -> None:
    cli, _, _, _ = build_local_context()

    handlers.help(cli, "show score")

    output = capsys.readouterr().out
    assert "show score" in output
    assert "Display the players' scores" in output
    assert "Available commands:" not in output


def test_hint_undo_redo_show_time_play_and_quit_cover_local_branches(monkeypatch, capsys) -> None:
    cli, game, client, server = build_local_context()

    handlers.hint(cli, client)
    game.provide_hint.return_value = "bad-move"
    handlers.hint(cli, client)
    game.provide_hint.return_value = ""
    handlers.hint(cli, client)

    before_history = SimpleNamespace(past_moves=[1], future_moves=[2])
    game.game_data.history = before_history
    game.undo.side_effect = lambda: None
    handlers.undo(cli, 1, client)
    game.undo.side_effect = lambda: (before_history.past_moves.pop(), before_history.future_moves.append(9))
    handlers.undo(cli, 2, client)

    redo_history = SimpleNamespace(past_moves=[1], future_moves=[2])
    game.game_data.history = redo_history
    game.redo.side_effect = lambda: None
    handlers.redo(cli, 1, client)
    game.redo.side_effect = lambda: (redo_history.future_moves.pop(), redo_history.past_moves.append(3))
    handlers.redo(cli, 2, client)

    game.get_game_configuration.return_value = {"blitz": False}
    handlers.show_time(cli)
    game.get_game_configuration.return_value = {"blitz": True}
    game.get_all_players_remaining_time_seconds.return_value = []
    handlers.show_time(cli)
    game.get_all_players_remaining_time_seconds.return_value = [(1, 65.0)]
    handlers.show_time(cli)
    handlers.show_time(cli, "oops")
    game.get_player_remaining_time_seconds.return_value = None
    handlers.show_time(cli, "3")
    game.get_player_remaining_time_seconds.return_value = 42.0
    handlers.show_time(cli, "3")

    class AIThenHumanGame:
        def __init__(self):
            self.current_player = DummyPlayer(2, is_ai=True)
            self.play_move = Mock(return_value=True)
            self.get_printed_board = Mock(return_value="BOARD")
            self.is_undo_history_empty = Mock(return_value=False)
            self.clear_undo_history = Mock()
            self.end_game = Mock(return_value=False)
            self.game_data = SimpleNamespace(
                history=SimpleNamespace(past_moves=[], future_moves=[]),
                players={
                    1: SimpleNamespace(get_score_int=lambda: 5),
                    2: SimpleNamespace(get_score_int=lambda: 3),
                },
            )

        def get_current_player(self):
            return self.current_player

        def get_players_order(self):
            return [1, 2]

        def play_ai_turn(self, _game):
            self.current_player = DummyPlayer(1, is_ai=False)

    ai_game = AIThenHumanGame()
    handlers.play(cli, "CFFF/0N0", ai_game, client)

    monkeypatch.setattr("builtins.input", lambda prompt="": "n")
    handlers.quit(cli, server, client)

    output = capsys.readouterr().out
    assert "and place a meeple on SW." in output
    assert "Hint: play move bad-move" in output
    assert "No hint available." in output
    assert "No move to undo." in output
    assert "Last 2 move(s) undone." in output
    assert "No move to redo." in output
    assert "Last 2 move(s) redone." in output
    assert "Blitz mode is disabled." in output
    assert "Remaining times:" in output
    assert "Usage: show time [PLAYER_ID]" in output
    assert "Unknown player: 3" in output
    assert "Remaining time for player 3: 00:42" in output
    assert "Quit command aborted." in output
    assert "Quitting the game. See you soon!" in output
    assert cli.running is False
    ai_game.clear_undo_history.assert_called_once_with()
    ai_game.get_printed_board.assert_called()


def test_connected_command_handlers_forward_to_server_and_quit_respects_server_state(
    capsys,
) -> None:
    cli, game, client, server = build_local_context()
    client.connected_to_a_server.return_value = True
    server.is_server_running.return_value = True

    handlers.new_game(cli, "1 2", client)
    handlers.load(cli, "save1", client)
    handlers.save(cli, "save2", client)
    handlers.shuffle(cli, client)
    handlers.draw(cli, client)
    handlers.hint(cli, client)
    handlers.undo(cli, 1, client)
    handlers.redo(cli, 1, client)
    handlers.show_hand(cli, client)
    handlers.show_history(cli, game, client)
    handlers.show_configuration(cli, game, client)
    handlers.set_parameter(cli, "ai_mode", "iterative", client)
    handlers.play(cli, "CFFF/0N0", game, client)
    handlers.show_board(cli, game, client)
    handlers.quit(cli, server, client)

    output = capsys.readouterr().out
    assert "You should close your server first." not in output
    client.send_to_server.assert_any_call("new 1 2")
    client.send_to_server.assert_any_call("load save1")
    client.send_to_server.assert_any_call("save save2")
    client.send_to_server.assert_any_call("shuffle")
    client.send_to_server.assert_any_call("draw")
    client.send_to_server.assert_any_call("hint")
    client.send_to_server.assert_any_call("undo")
    client.send_to_server.assert_any_call("redo")
    client.send_to_server.assert_any_call("show hand")
    client.send_to_server.assert_any_call("show history")
    client.send_to_server.assert_any_call("show configuration")
    client.send_to_server.assert_any_call("set ai_mode=iterative")
    client.send_to_server.assert_any_call("play CFFF/0N0")
    client.send_to_server.assert_any_call("board")
    client.send_to_server.assert_any_call("quit")
