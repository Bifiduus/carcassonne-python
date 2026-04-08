import socket
from unittest.mock import Mock


from carcassonne.business_logic.server import Server
from carcassonne.datas.datas_factory import DatasFactory


class FakeSocket:
    def __init__(
        self,
        bind_error=None,
        send_error=None,
        close_error=None,
    ) -> None:
        self.bind_error = bind_error
        self.send_error = send_error
        self.close_error = close_error
        self.bound = None
        self.closed = False
        self.sent = []

    def setsockopt(self, *args, **kwargs):
        return None

    def bind(self, address):
        if self.bind_error is not None:
            raise self.bind_error
        self.bound = address

    def listen(self):
        return None

    def settimeout(self, timeout):
        self.timeout = timeout

    def close(self):
        self.closed = True
        if self.close_error is not None:
            raise self.close_error

    def send(self, data):
        if self.send_error is not None:
            raise self.send_error
        self.sent.append(data)

    def sendall(self, data):
        if self.send_error is not None:
            raise self.send_error
        self.sent.append(data)


class FakeAcceptingServerSocket(FakeSocket):
    def __init__(self, accepted_client=None, accept_error=None) -> None:
        super().__init__()
        self.accepted_client = accepted_client or FakeSocket()
        self.accept_error = accept_error
        self.accept_calls = 0

    def accept(self):
        self.accept_calls += 1
        if self.accept_error is not None:
            raise self.accept_error
        return self.accepted_client, ("127.0.0.1", 9999)


class FakeBroadcastSocket(FakeSocket):
    def __init__(self) -> None:
        super().__init__()
        self.broadcasts = []

    def sendto(self, data, address):
        self.broadcasts.append((data, address))


class FakeRecvSocket(FakeSocket):
    def __init__(self, messages, send_error=None, close_error=None) -> None:
        super().__init__(send_error=send_error, close_error=close_error)
        self.messages = list(messages)

    def recv(self, size):
        item = self.messages.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def make_server(monkeypatch, repo=None):
    monkeypatch.setattr(
        "carcassonne.business_logic.server.socket.gethostname", lambda: "host")
    monkeypatch.setattr(
        "carcassonne.business_logic.server.socket.gethostbyname", lambda host: "127.0.0.1")
    return Server(repo=repo or Mock(), datas_factory=DatasFactory())


def test_server_start_and_basic_helpers(monkeypatch, capsys) -> None:
    repo = Mock()
    repo.is_database_closed.return_value = False
    server = make_server(monkeypatch, repo)
    fake_socket = FakeSocket()
    fake_thread = Mock()

    monkeypatch.setattr(
        "carcassonne.business_logic.server.socket.socket",
        lambda *args, **kwargs: fake_socket,
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.server.Thread",
        lambda *args, **kwargs: fake_thread,
    )

    server.server_start("")

    assert fake_socket.bound == ("", 12345)
    assert server.is_server_running() is True
    fake_thread.start.assert_called_once_with()
    captured = capsys.readouterr()
    assert "Server started on port 12345" in (captured.out + captured.err)

    server.registered_clients = {"sock": True}
    assert server.client_is_registered("sock") is True
    assert server.client_is_registered("missing") is False

    bad_server = make_server(monkeypatch, repo)
    monkeypatch.setattr(
        "carcassonne.business_logic.server.socket.socket",
        lambda *args, **kwargs: FakeSocket(bind_error=OSError("boom")),
    )
    bad_server.server_start("9999")
    captured = capsys.readouterr()
    assert "Error starting server: boom" in (captured.out + captured.err)


def test_server_repository_player_and_profile_helpers(monkeypatch) -> None:
    repo = Mock()
    repo.check_all_remaining_timeouts.return_value = [1]
    repo.get_host_from_party.return_value = 1
    repo.check_all_invitations_resolved.return_value = True
    repo.party_is_launched.return_value = False
    repo.get_username.side_effect = lambda client_id: {
        "1": "Alice", "2": "Bob", 1: "Alice", 2: "Bob"}[client_id]
    repo.player_exists.side_effect = lambda username: username == "Alice"
    repo.get_player_profile.return_value = {
        "username": "Alice",
        "status": "idle",
        "score": 4,
        "stats_win": 3,
        "stats_lose": 1,
    }
    repo.get_id_from_username.side_effect = lambda username: {
        "Alice": 1, "Bob": 2}[username]
    repo.get_status.side_effect = lambda player_id: {
        "1": "idle", "2": "away"}[player_id]
    server = make_server(monkeypatch, repo)

    server.check_client_timeouts()
    repo.check_all_remaining_timeouts.assert_called_once_with(
        server.CLIENT_TIMEOUT)
    assert server.party_can_be_launched(7) is True
    repo.party_is_launched.return_value = True
    assert server.party_can_be_launched(7) is False

    assert server.check_clients_list_validity(["1", "2"]) == ["1"]
    players = server.create_players_from_list([1, 2])
    assert [player.get_username() for player in players] == ["Alice", "Bob"]

    profile = server.check_profile_player(1)
    assert "username=Alice" in profile
    repo.get_player_profile.return_value = None
    assert server.check_profile_player(1) == "Player not found\n"

    server.player_clients = {object(): "Alice", object(): "Bob"}
    connected_players = server.get_connected_players()
    assert {"id": "1", "name": "Alice", "status": "idle"} in connected_players
    assert {"id": "2", "name": "Bob", "status": "away"} in connected_players

    server.current_games_list = {1: ("A", object()), 2: ("B", object())}
    assert server.number_current_games() == 2

    server.get_connected_players = Mock(
        return_value=[{"id": "1", "status": "idle"}])
    assert server.start_new_game_with_players(
        []) == "Error: No player IDs provided"
    assert server.start_new_game_with_players(
        ["2"]) == "Error: Player 2 is not connected"
    server.get_connected_players.return_value = [{"id": "2", "status": "away"}]
    assert server.start_new_game_with_players(
        ["2"]) == "Error: Player 2 is not idle"
    server.get_connected_players.return_value = [
        {"id": "1", "status": "idle"},
        {"id": "2", "status": "idle"},
    ]
    server.create_new_party = Mock()
    assert server.start_new_game_with_players(
        ["1", "2"]) == "New game started with players: 1, 2"
    server.create_new_party.assert_called_once_with([1, 2], "1")


def test_server_process_message_and_send_helpers(monkeypatch, capsys) -> None:
    repo = Mock()
    repo.get_username.return_value = "Alice"
    server = make_server(monkeypatch, repo)
    server.server = object()
    server.handle_communication = Mock()
    server.handle_communication.command_ping.return_value = "pong"
    server.handle_communication.command_quit.return_value = "bye"
    server.handle_communication.command_server_status.return_value = "status"
    server.handle_communication.command_new.return_value = "new"
    server.handle_communication.command_players.return_value = "players"
    server.handle_communication.command_play.return_value = "play"
    server.handle_communication.command_scoreboard.return_value = "scoreboard"
    server.handle_communication.command_accept.return_value = "accept"
    server.handle_communication.command_decline.return_value = "decline"
    server.handle_communication.command_cancel.return_value = "cancel"
    server.handle_communication.command_away.return_value = "away"
    server.handle_communication.command_back.return_value = "back"
    server.handle_communication.command_board.return_value = "board"
    server.handle_communication.command_set.return_value = "set"
    server.handle_communication.command_config.return_value = "config"
    server.handle_communication.command_history.return_value = "history"
    server.handle_communication.command_score.return_value = "score"
    server.handle_communication.command_hand.return_value = "hand"
    server.handle_communication.command_redo.return_value = "redo"
    server.handle_communication.command_undo.return_value = "undo"
    server.handle_communication.command_hint.return_value = "hint"
    server.handle_communication.command_draw.return_value = "draw"
    server.handle_communication.command_shuffle.return_value = "shuffle"
    server.handle_communication.command_save.return_value = "save"
    server.handle_communication.command_load.return_value = "load"

    cases = {
        "ping": "pong",
        "Bad client disconnection": "bye",
        "server status": "status",
        "new 1 2": "new",
        "players": "players",
        "play CFFF/0N0": "play",
        "scoreboard": "scoreboard",
        "accept": "accept",
        "decline": "decline",
        "cancel 2": "cancel",
        "away": "away",
        "back": "back",
        "board": "board",
        "set ai=random": "set",
        "show configuration": "config",
        "show history": "history",
        "show score": "score",
        "show hand": "hand",
        "redo": "redo",
        "undo": "undo",
        "hint": "hint",
        "draw": "draw",
        "shuffle": "shuffle",
        "save game1": "save",
        "load game1": "load",
    }
    for message, expected in cases.items():
        assert server.process_message("1", message) == expected

    repo.set_unproper_client.assert_called_once_with("Alice")
    server.server = None
    assert server.process_message("1", "ping") == ""

    socket_ok = FakeSocket()
    socket_bad = FakeSocket(send_error=RuntimeError("boom"))
    server.client_sockets = {"Alice": socket_ok, "Bob": socket_bad}
    server.player_clients = {socket_ok: "Alice", socket_bad: "Bob"}
    repo.get_id_from_username.side_effect = lambda username: {
        "Alice": 1, "Bob": 2}[username]
    server.send_to_clients("hello\n")
    assert socket_ok.sent[0] == b"Server -> Client1: hello\n"
    captured = capsys.readouterr()
    assert "Error handling client: boom" in (captured.out + captured.err)
    server.client_sockets = {"Alice": socket_ok}
    assert server.send_to_client("Alice", "hi") is True
    assert server.send_to_client("Missing", "hi") is False
    bad_socket = FakeSocket(send_error=RuntimeError("boom"))
    server.client_sockets = {"Bob": bad_socket}
    assert server.send_to_client("Bob", "hi") is False


def test_server_registration_invitations_party_management_and_cleanup(
    monkeypatch, capsys
) -> None:
    repo = Mock()
    repo.registering.return_value = True
    repo.is_proper_client.return_value = True
    repo.get_id_from_username.side_effect = lambda username: {
        "Alice": 1, "Bob": 2}[username]
    repo.get_username.side_effect = lambda player_id: {
        "1": "Alice", "2": "Bob", 1: "Alice", 2: "Bob"}[player_id]
    repo.send_invitation.return_value = True
    repo.get_party_id.return_value = 7
    repo.get_game_id.return_value = 99
    repo.get_status.return_value = "idle"
    server = make_server(monkeypatch, repo)

    client_socket = FakeSocket()
    server.handle_client_registering(
        "username=Alice password=pw", client_socket, 1)
    assert server.registered_clients[client_socket] is True
    assert server.client_sockets["Alice"] is client_socket
    assert server.player_clients[client_socket] == "Alice"
    assert client_socket.sent[-1] == b"Server -> Client1: Successfull registering !\n"

    timeout_socket = FakeSocket()
    repo.registering.return_value = False
    server.handle_client_registering("bad-message", timeout_socket, 2)
    assert timeout_socket.sent[-1] == b"Server -> Client2: You should send your username and password !\n"

    repo.registering.return_value = True
    repo.is_proper_client.return_value = False
    repo.get_remaining_timeout.return_value = 12
    late_socket = FakeSocket()
    server.handle_client_registering(
        "username=Bob password=pw", late_socket, 2)
    repo.get_remaining_timeout.assert_called_once_with("Bob")
    assert late_socket.sent[-1] == b"Server -> Client2: Your registration has failed...\n"

    invited_socket = FakeSocket()
    server.client_sockets = {"Bob": invited_socket}
    server.send_invitation("2", "1")
    assert invited_socket.sent
    server.send_invitation("3", "1")
    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert (
        "Error sending invitation" in output
        or "Client socket not found for 3" in output
    )

    fake_party_game = Mock()
    # Store the original factories before mocking
    original_datas_create = server.datas_factory.create
    original_bl_create = server.business_logic_factory.create

    def mock_datas_factory_create(class_name, *args, **kwargs):
        if class_name == "GraphData":
            return Mock()  # Return a mock GraphData
        # Delegate to real factory for other classes
        return original_datas_create(class_name, *args, **kwargs)

    def mock_bl_factory_create(class_name, *args, **kwargs):
        if class_name == "Game":
            return fake_party_game  # Return the mock game
        # Delegate to real factory for other classes
        return original_bl_create(class_name, *args, **kwargs)

    server.datas_factory.create = Mock(side_effect=mock_datas_factory_create)
    server.business_logic_factory.create = Mock(
        side_effect=mock_bl_factory_create)
    repo.get_game_id.return_value = 99
    message = server.create_new_party([1, 2], "1", "Party X")
    assert message == "Your party has been created successfully !\n"
    fake_party_game.start_online_game.assert_called_once()
    assert 99 in server.current_games_list

    repo.get_parties.return_value = [7]
    server.party_can_be_launched = Mock(return_value=True)
    repo.get_host_from_party.return_value = 1
    repo.get_party.return_value = [1]
    server.send_to_client = Mock()
    server.launch_availables_games()
    server.send_to_client.assert_called_once_with(
        "Alice", "You cannot play alone...")

    repo.get_party.return_value = [1, 2]
    server.create_new_party = Mock()
    server.launch_availables_games()
    server.create_new_party.assert_called_once_with([1, 2], "1")

    ended_game = Mock()
    ended_game.end_game.return_value = True
    player1 = Mock()
    player1.score.score = 10
    player2 = Mock()
    player2.score.score = 5
    ended_game.game_data.players = {1: player1, 2: player2}
    server.current_games_list = {99: ("Party", ended_game)}
    repo.get_group_from_game.return_value = 99
    repo.check_party_is_alive.return_value = True
    server.clean_finished_games()
    repo.clean_party.assert_called_once_with(99)
    assert server.current_games_list == {}


def test_server_stop_get_game_and_server_state_cleanup(monkeypatch, capsys) -> None:
    repo = Mock()
    repo.get_party_id.return_value = 7
    repo.get_game_id.return_value = 99
    repo.get_players_from_group.return_value = ["Alice"]
    server = make_server(monkeypatch, repo)
    game = Mock()
    server.current_games_list = {99: ("Party", game)}
    assert server.get_game("1") is game

    server.server_thread = Mock()
    server.server_thread.is_alive.return_value = False
    server.server = FakeSocket()
    client_socket = FakeSocket()
    server.connected_clients = [client_socket]
    server.player_clients = {client_socket: "Alice"}
    server.client_sockets = {"Alice": client_socket}
    server.registered_clients = {client_socket: True}
    client_thread = Mock()
    client_thread.is_alive.return_value = False
    server.client_threads = [client_thread]

    backup_game = Mock()
    server.current_games_list = {99: ("Party", backup_game)}
    server.server_stop()

    repo.client_quit.assert_called_once_with("Alice")
    backup_game.save_game_to_file.assert_called_once()
    repo.close.assert_called_once_with()
    assert server.current_games_list == {}
    assert server.connected_clients == []
    assert server.client_sockets == {}
    assert server.player_clients == {}
    assert server.registered_clients == {}
    captured = capsys.readouterr()
    assert "Server shutdown complete" in (captured.out + captured.err)


def test_server_running_accepts_clients_broadcasts_and_checks_timeouts(
    monkeypatch, capsys
) -> None:
    repo = Mock()
    repo.check_all_invitations_timeout.return_value = [1]
    repo.get_username.return_value = "Alice"
    server = make_server(monkeypatch, repo)
    accepted_client = FakeSocket()
    server_socket = FakeAcceptingServerSocket(accepted_client=accepted_client)
    udp_socket = FakeBroadcastSocket()
    spawned_threads = []

    class FakeThread:
        def __init__(self, *args, **kwargs) -> None:
            self.args = args
            self.kwargs = kwargs
            self.started = False
            spawned_threads.append(self)

        def start(self):
            self.started = True

    server.server = server_socket
    server.should_stop.set()
    server.send_to_client = Mock()
    server.launch_availables_games = Mock()
    server.clean_finished_games = Mock()

    def fake_check_client_timeouts():
        server.should_stop.clear()

    server.check_client_timeouts = Mock(side_effect=fake_check_client_timeouts)

    monkeypatch.setattr(
        "carcassonne.business_logic.server.select.select",
        lambda *args, **kwargs: ([server_socket], [], []),
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.server.Thread",
        FakeThread,
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.server.socket.socket",
        lambda *args, **kwargs: udp_socket,
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.server.time.time",
        lambda: 0.0,
    )

    server.server_running("4242")

    assert server.connected_clients == [accepted_client]
    assert server.registered_clients[accepted_client] is False
    assert len(server.client_threads) == 1
    assert spawned_threads[0].started is True
    server.send_to_client.assert_called_once_with(
        "Alice", "Your invitation timed out.."
    )
    server.launch_availables_games.assert_called_once_with()
    server.clean_finished_games.assert_called_once_with()
    server.check_client_timeouts.assert_called_once_with()
    assert udp_socket.broadcasts == [
        (b"127.0.0.1:4242", ("<broadcast>", 12346))
    ]
    captured = capsys.readouterr()
    assert "Accepted connection from a client." in (
        captured.out + captured.err)


def test_server_running_handles_timeout_then_generic_error(
    monkeypatch, capsys
) -> None:
    repo = Mock()
    repo.check_all_invitations_timeout.return_value = []
    server = make_server(monkeypatch, repo)
    server.server = FakeSocket()
    server.should_stop.set()
    outcomes = iter([socket.timeout("wait"), RuntimeError("boom")])

    def fake_select(*args, **kwargs):
        outcome = next(outcomes)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(
        "carcassonne.business_logic.server.select.select",
        fake_select,
    )

    server.server_running("4242")

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "Error accepting connection: boom" in output
    assert "Server stopped." in output


def test_handle_client_registers_processes_messages_and_cleans_up(
    monkeypatch,
) -> None:
    repo = Mock()
    repo.registering.return_value = True
    repo.get_id_from_username.side_effect = lambda username: {"Alice": 1}[
        username
    ]
    repo.is_proper_client.side_effect = [True, False]
    server = make_server(monkeypatch, repo)
    server.server = object()
    server.handle_communication = Mock()
    server.handle_communication.command_ping.return_value = "pong"
    server.handle_communication.command_quit.return_value = "bye"
    client_socket = FakeRecvSocket(
        [
            b"Alice: username=Alice password=pw",
            b"Alice: ping",
            b"Alice: quit",
        ]
    )
    server.connected_clients = [client_socket]
    server.registered_clients = {client_socket: False}

    server.handle_client(client_socket)

    assert client_socket.closed is True
    assert any(message.endswith(b"Successfull registering !\n")
               for message in client_socket.sent)
    assert any(message.endswith(b"pong\n") for message in client_socket.sent)
    repo.set_timeout_for_player.assert_called_once_with(
        "Alice", server.CLIENT_TIMEOUT
    )
    assert server.handle_communication.command_quit.call_count == 2
    assert client_socket not in server.connected_clients
    assert server.client_sockets == {}
    assert server.player_clients == {}
    assert server.registered_clients == {}


def test_handle_client_marks_improper_clients_on_processing_errors(
    monkeypatch, capsys
) -> None:
    repo = Mock()
    repo.get_id_from_username.return_value = 1
    repo.is_proper_client.return_value = False
    server = make_server(monkeypatch, repo)
    server.server = object()
    server.handle_communication = Mock()
    server.handle_communication.command_ping.side_effect = RuntimeError("boom")
    server.handle_communication.command_quit.return_value = "bye"
    client_socket = FakeRecvSocket([b"Alice: ping"])
    server.connected_clients = [client_socket]
    server.registered_clients = {client_socket: True}
    server.player_clients = {client_socket: "Alice"}
    server.client_sockets = {"Alice": client_socket}

    server.handle_client(client_socket)

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "Error handling client: boom" in output
    repo.set_unproper_client.assert_called_once_with("Alice")
    repo.set_timeout_for_player.assert_called_once_with(
        "Alice", server.CLIENT_TIMEOUT
    )
    assert client_socket not in server.connected_clients


def test_server_stop_logs_errors_and_thread_warnings(monkeypatch, capsys) -> None:
    repo = Mock()
    repo.client_quit.side_effect = RuntimeError("quit fail")
    repo.close.side_effect = RuntimeError("repo fail")
    server = make_server(monkeypatch, repo)

    server.server_thread = Mock()
    server.server_thread.is_alive.return_value = True
    server.server = FakeSocket(close_error=RuntimeError("close fail"))
    client_socket = FakeSocket(
        send_error=RuntimeError("send fail"),
        close_error=RuntimeError("client close fail"),
    )
    server.connected_clients = [client_socket]
    server.player_clients = {client_socket: "Alice"}
    server.client_sockets = {"Alice": client_socket}
    server.registered_clients = {client_socket: True}

    client_thread = Mock()
    client_thread.is_alive.return_value = True
    server.client_threads = [client_thread]

    backup_game = Mock()
    backup_game.save_game_to_file.side_effect = RuntimeError("backup fail")
    server.current_games_list = {99: ("Party", backup_game)}

    server.server_stop()

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "Error closing server socket: close fail" in output
    assert "Error sending shutdown message: send fail" in output
    assert "Error closing client socket: client close fail" in output
    assert "Error cleaning up game 99: backup fail" in output
    assert "Warning: a client thread did not finish in time" in output
    assert "Error closing repository: repo fail" in output
    assert "Warning: server thread did not terminate within timeout" in output


def test_server_starting_game_and_invitation_cover_additional_error_paths(
    monkeypatch, capsys
) -> None:
    repo = Mock()
    repo.get_username.side_effect = lambda player_id: {"1": "Alice", "2": "Bob"}[
        player_id
    ]
    repo.get_party_id.return_value = 8
    server = make_server(monkeypatch, repo)

    server.send_invitation("2", "1")
    captured = capsys.readouterr()
    assert "Client Bob is not connected" in (captured.out + captured.err)

    fake_party_game = Mock()

    # Store original factories for delegation
    original_datas_create = server.datas_factory.create
    original_bl_create = server.business_logic_factory.create

    def mock_datas_factory_create(class_name, *args, **kwargs):
        if class_name == "GraphData":
            return Mock()
        return original_datas_create(class_name, *args, **kwargs)

    def mock_bl_factory_create(class_name, *args, **kwargs):
        if class_name == "Game":
            return fake_party_game
        return original_bl_create(class_name, *args, **kwargs)

    server.datas_factory.create = Mock(side_effect=mock_datas_factory_create)
    server.business_logic_factory.create = Mock(
        side_effect=mock_bl_factory_create)
    repo.create_game.side_effect = RuntimeError("db fail")
    message = server.create_new_party([1, 2], "1")

    assert message == "Your party has been created successfully !\n"
    captured = capsys.readouterr()
    assert "Error creating party in repository: db fail" in (
        captured.out + captured.err)

    server.get_connected_players = Mock(
        return_value=[
            {"id": "1", "status": "idle"},
            {"id": "2", "status": "idle"},
        ]
    )
    server.create_new_party = Mock(side_effect=RuntimeError("cannot start"))
    assert (
        server.start_new_game_with_players(["1", "2"])
        == "Error starting game: cannot start"
    )
