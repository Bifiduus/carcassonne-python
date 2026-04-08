from types import SimpleNamespace
from unittest.mock import Mock

from carcassonne.business_logic.online_communication import OnlineCommunication


class DummyPlayer:
    def __init__(self, player_id: int, username: str, score, is_ai: bool = False):
        self.player_id = player_id
        self.username = username
        self.score = score
        self.is_ai = is_ai

    def get_id(self) -> int:
        return self.player_id

    def get_username(self) -> str:
        return self.username


def build_online_context(
    *,
    party_id=7,
    game_id=99,
    current_player_id=1,
    ended=False,
    play_result=True,
    hand=None,
    draw_tile_result="CFFF",
    save_result=0,
    load_result=0,
):
    current_player = SimpleNamespace(get_id=lambda: current_player_id)
    players = {
        1: DummyPlayer(1, "Alice", 12, is_ai=False),
        2: DummyPlayer(2, "Bot", 9, is_ai=True),
    }
    game = SimpleNamespace(
        get_current_player=lambda: current_player,
        end_game=lambda: ended,
        play_move=Mock(return_value=play_result),
        get_printed_board=lambda: "BOARD",
        set_game_configuration=Mock(),
        get_game_configuration=lambda: {"blitz": True, "ai_mode": "random"},
        get_history=lambda: ["0:CFFF/0N0;", "1:FFFF/m/1E0;"],
        score_manager=SimpleNamespace(
            score_end_of_game=Mock(),
            score_end_of_turn=Mock(),
        ),
        game_data=SimpleNamespace(
            graph=object(),
            players=players,
            current_hand=hand,
            shuffle_algo="fisher-yates",
        ),
        redo=Mock(),
        undo=Mock(),
        provide_hint=Mock(return_value="CFFF/0N0"),
        draw_tile=Mock(return_value=draw_tile_result),
        shuffle_deck=Mock(return_value=321),
        save_game_to_file=Mock(return_value=save_result),
        load_game_from_file=Mock(return_value=load_result),
    )

    repo = SimpleNamespace(
        client_quit=Mock(),
        get_username=Mock(side_effect=lambda client_id: {
                          1: "Alice", 2: "Bob", "1": "Alice", "2": "Bob"}[client_id]),
        create_party=Mock(),
        current_players=Mock(return_value="players-list"),
        get_scoreboard=Mock(
            return_value=[
                {
                    "id": 1,
                    "username": "Alice",
                    "victories": 3,
                    "defeats": 1,
                    "total_games": 4,
                }
            ]
        ),
        invitation_received=Mock(return_value=(-1, -1)),
        accept_invitation=Mock(),
        reject_invitation=Mock(),
        invitation_sent_from=Mock(return_value=[]),
        cancel_invitation_from=Mock(return_value="cancelled"),
        change_status=Mock(side_effect=lambda client,
                           status: f"Status changed to {status}."),
        get_party_id=Mock(return_value=party_id),
        get_game_id=Mock(return_value=game_id),
        get_group=Mock(return_value=party_id),
        get_host_from_party=Mock(return_value=1),
    )

    server = SimpleNamespace(
        repo=repo,
        server=SimpleNamespace(getsockname=lambda: ("0.0.0.0", 4242)),
        connected_clients=[1, 2],
        current_games_list={game_id: ("match", game)},
        client_sockets={},
        check_clients_list_validity=Mock(return_value=["2", "3"]),
        send_invitation=Mock(),
        check_profile_player=Mock(return_value="profile"),
        send_to_group=Mock(),
        send_to_group_except=Mock(),
    )

    return OnlineCommunication(server), server, repo, game


def test_online_communication_basic_commands_and_invitations() -> None:
    communication, server, repo, _ = build_online_context()

    assert "pong" in communication.command_ping("ping 0")
    assert communication.command_quit("Alice") == "Bye Alice!\n"
    assert "Port: 4242" in communication.command_server_status()
    assert communication.command_new(
        "new", "1") == "You cannot create an empty party !"
    assert communication.command_new("new 2 3", "1") == "Invitation(s) sent."
    repo.create_party.assert_called_once_with("Alice")
    server.send_invitation.assert_any_call("2", "1")
    server.send_invitation.assert_any_call("3", "1")
    assert communication.command_players("players") == "players-list"
    assert communication.command_players("players 2") == "profile"
    assert "Scoreboard:" in communication.command_scoreboard()
    assert communication.command_cancel("1", "") == "No invitations to cancel."
    repo.invitation_sent_from.return_value = ["2"]
    assert communication.command_cancel("1", "2 3") == "cancelled"
    assert communication.command_away("Alice") == "Status changed to away."
    assert communication.command_back("Alice") == "Status changed to idle."


def test_online_communication_accept_decline_and_host_notifications() -> None:
    communication, server, repo, _ = build_online_context()
    host_socket = Mock()
    server.client_sockets = {1: host_socket}

    assert communication.command_accept(
        "2") == "You have no invitation to accept.\n"
    assert communication.command_decline(
        "2") == "You have no invitation to decline.\n"

    repo.invitation_received.side_effect = [(1, 7), (1, 7), (1, 7), (1, 7)]
    assert communication.command_accept("2") == "Invitation accepted !\n"
    repo.accept_invitation.assert_called_once_with(7, "2")
    host_socket.send.assert_called()
    sent_message = host_socket.send.call_args[0][0].decode()
    assert "Bob has accepted your invitation!" in sent_message

    host_socket.reset_mock()
    repo.invitation_received.side_effect = [(1, 7), (1, 7)]
    assert communication.command_decline("2") == "Invitation declined !\n"
    repo.reject_invitation.assert_called_once_with("2")
    sent_message = host_socket.send.call_args[0][0].decode()
    assert "Bob has rejected your invitation!" in sent_message

    host_socket.send.side_effect = RuntimeError("boom")
    communication.notify_host_of_acceptance(1, "2")
    communication.notify_host_of_rejection(1, "2")


def test_online_communication_gameplay_commands_cover_play_board_set_config_and_history() -> None:
    communication, server, repo, game = build_online_context()

    repo.get_party_id.return_value = -1
    assert communication.command_play(
        "play CFFF/0N0", "1") == "You are not in a game."
    assert communication.command_board("1") == "You are not in a game."
    assert communication.command_history("1") == "You are not in a game."

    repo.get_party_id.return_value = 7
    game.get_current_player = lambda: SimpleNamespace(get_id=lambda: 2)
    assert communication.command_play(
        "play CFFF/0N0", "1") == "It is not your turn to play"

    game.get_current_player = lambda: SimpleNamespace(get_id=lambda: 1)
    game.end_game = lambda: True
    assert "You cannot play when the game is ended." in communication.command_play(
        "play CFFF/0N0", "1")

    game.end_game = lambda: False
    game.play_move.return_value = True
    assert communication.command_play(
        "play CFFF/0N0", "1").startswith("Move played.\nBOARD\n")
    server.send_to_group_except.assert_called_with(
        7, "OPPONENT_MOVE played move. Board:\nBOARD\n", "Alice")

    game.play_move.return_value = False
    assert communication.command_play(
        "play CFFF/0N0", "1").startswith("Move not played.\nBOARD\n")
    assert communication.command_board("1") == "Game board:\nBOARD"

    assert communication.command_set(
        "1", "set ai_mode=minimax") == "Parameter 'ai_mode' set to 'minimax'."
    game.set_game_configuration.assert_called_with("ai_mode", "minimax")
    assert "Current game configuration:" in communication.command_config("1")
    assert "Current history:" in communication.command_history("1")


def test_online_communication_score_hand_undo_redo_hint_draw_shuffle_save_and_load() -> None:
    communication, server, repo, game = build_online_context(hand=None)

    repo.get_party_id.return_value = -1
    assert communication.command_score("1") == "You are not in a game."
    assert communication.command_hand("1") == "You are not in a game."
    assert communication.command_redo("1") == "You are not in a game."
    assert communication.command_undo("1") == "You are not in a game."
    assert communication.command_hint("1") == "You are not in a game."
    assert communication.command_draw("1") == "You are not in a game."
    assert communication.command_shuffle("1") == "You are not in a game."
    assert communication.command_save(
        "1", "save game1") == "You are not in a game."
    assert communication.command_load(
        "1", "load game1") == "You are not in a game."

    repo.get_party_id.return_value = 7
    game.end_game = lambda: False
    score_answer = communication.command_score("1")
    game.score_manager.score_end_of_turn.assert_called_once()
    assert "Alice: 12 points." in score_answer
    assert "Bot AI: 9 points." in score_answer

    game.end_game = lambda: True
    communication.command_score("1")
    game.score_manager.score_end_of_game.assert_called_once()

    assert communication.command_hand("1") == "No tile in hand."
    game.game_data.current_hand = "CFFF"
    assert communication.command_hand("1") == "Tile in hand: CFFF"

    game.get_current_player = lambda: SimpleNamespace(get_id=lambda: 2)
    assert communication.command_redo("1") == "It is not your turn to play"
    assert communication.command_undo("1") == "It is not your turn to play"
    assert communication.command_draw("1") == "It is not your turn to play"
    assert communication.command_shuffle("1") == "It is not your turn to play"
    assert communication.command_save(
        "1", "save game1") == "It is not your turn to play"
    assert communication.command_load(
        "1", "load game1") == "It is not your turn to play"

    game.get_current_player = lambda: SimpleNamespace(get_id=lambda: 1)
    assert communication.command_hint("1") == "CFFF/0N0"
    assert communication.command_redo("1") == "Last moves redone."
    game.redo.assert_called_once_with()
    server.send_to_group_except.assert_called_with(
        7,
        "OPPONENT_MOVE redone moves. Board:\nBOARD\n",
        "Alice",
    )
    assert communication.command_undo("1") == "Last moves undone."
    game.undo.assert_called_once_with()
    server.send_to_group_except.assert_called_with(
        7,
        "OPPONENT_MOVE undone moves. Board:\nBOARD\n",
        "Alice",
    )

    game.game_data.current_hand = None
    game.draw_tile.return_value = None
    assert communication.command_draw("1") == "The deck is empty!"
    game.game_data.current_hand = "OLD"
    game.draw_tile.return_value = "NEW"
    assert communication.command_draw(
        "1") == "You already have a tile in hand."
    game.game_data.current_hand = None
    game.draw_tile.return_value = "CFFF"
    assert communication.command_draw("1") == "Tile drawn: CFFF"
    server.send_to_group_except.assert_called_with(
        7,
        "OPPONENT_MOVE drew a tile.\n",
        "Alice",
    )

    assert "Deck shuffled. Algorithm: fisher-yates. Seed: 321" == communication.command_shuffle(
        "1")
    assert communication.command_save(
        "1", "save game1") == "Game saved to game1."
    game.save_game_to_file.return_value = -1
    assert communication.command_save(
        "1", "save game1") == "Failed to save the game to game1."
    assert communication.command_load(
        "1", "load game1") == "Game loaded from game1."
    game.load_game_from_file.return_value = -1
    assert communication.command_load(
        "1", "load game1") == "Failed to load the game from game1."
