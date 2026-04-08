from types import SimpleNamespace
from unittest.mock import Mock, patch


from carcassonne.business_logic.client import Client


def build_repo():
    repo = Mock()
    repo.is_accounted_for.return_value = True
    repo.get_online_player.return_value = "alice"
    repo.has_no_special_username.return_value = True
    repo.get_password.return_value = "pw"
    repo.get_next_available_id.return_value = 5
    repo.create_default_online_player.return_value = "created"
    return repo


def build_client(repo=None):
    repo = repo or build_repo()
    server_service = SimpleNamespace(server_name="127.0.0.1")
    return Client(repo, server_service), repo, server_service


class FakeTCPSocket:
    def __init__(self, connect_error=None, close_error=None) -> None:
        self.connect_error = connect_error
        self.close_error = close_error
        self.connected = None
        self.timeout = None
        self.closed = False
        self.sent = []
        self.shutdown_calls = []

    def settimeout(self, value):
        self.timeout = value

    def connect(self, address):
        if self.connect_error is not None:
            raise self.connect_error
        self.connected = address

    def sendall(self, data):
        self.sent.append(data)

    def recv(self, size):
        return b"Server -> Client1: pong\n"

    def shutdown(self, how):
        self.shutdown_calls.append(how)

    def close(self):
        self.closed = True
        if self.close_error is not None:
            raise self.close_error


class FakeUDPSocket:
    def __init__(self, messages=None, bind_error=None) -> None:
        self.messages = list(messages or [])
        self.bind_error = bind_error
        self.bound = None
        self.timeout = None
        self.closed = False

    def bind(self, address):
        if self.bind_error is not None:
            raise self.bind_error
        self.bound = address

    def settimeout(self, value):
        self.timeout = value

    def recvfrom(self, size):
        return self.messages.pop(0)

    def close(self):
        self.closed = True


def test_client_init_handles_account_creation_and_existing_account(monkeypatch, capsys) -> None:
    repo = build_repo()
    repo.is_accounted_for.return_value = False
    server_service = SimpleNamespace(server_name="127.0.0.1")

    with patch("builtins.input", side_effect=["alice", "pw"]):
        client = Client(repo, server_service)

    assert client.client_player == "alice"
    repo.create_default_online_player.assert_called_once_with(
        "alice", "pw", "127.0.0.1"
    )
    assert "You should create an online account." in capsys.readouterr().out

    client, repo, _ = build_client()
    assert client.client_player == "alice"


def test_join_server_covers_missing_server_success_and_connection_error(
    monkeypatch, capsys
) -> None:
    client, repo, server_service = build_client()

    assert client.join_server("10.0.0.1") is False
    captured = capsys.readouterr()
    assert "there is no server with that IP address" in (
        captured.out + captured.err)

    client.available_servers = {"10.0.0.1": (4242, 0.0)}
    fake_socket = FakeTCPSocket()
    fake_thread = Mock()
    monkeypatch.setattr("carcassonne.business_logic.client.socket.socket",
                        lambda *args, **kwargs: fake_socket)
    monkeypatch.setattr("carcassonne.business_logic.client.threading.Thread",
                        lambda *args, **kwargs: fake_thread)
    sent_messages = []
    client.send_to_server = lambda text: sent_messages.append(text) or True

    assert client.join_server("10.0.0.1") is True
    assert fake_socket.connected == ("10.0.0.1", 4242)
    assert client.connected_server == "10.0.0.1"
    assert client.has_joined_server is True
    assert sent_messages == ["username=alice password=pw"]
    fake_thread.start.assert_called_once_with()

    client, repo, _ = build_client()
    client.available_servers = {"10.0.0.1": (4242, 0.0)}
    error_socket = FakeTCPSocket(connect_error=OSError("boom"))
    monkeypatch.setattr("carcassonne.business_logic.client.socket.socket",
                        lambda *args, **kwargs: error_socket)

    assert client.join_server("10.0.0.1") is False
    assert client.client is None
    captured = capsys.readouterr()
    assert "Unable to connect to 10.0.0.1:4242" in (
        captured.out + captured.err)


def test_join_server_defaults_to_current_server_name_and_uses_server_specific_username(
    monkeypatch,
) -> None:
    client, repo, server_service = build_client()
    client.available_servers = {"127.0.0.1": (4242, 0.0)}
    repo.has_no_special_username.return_value = False
    repo.get_online_player.side_effect = lambda server: {
        "127.0.0.1": "alice-remote"
    }[server]
    fake_socket = FakeTCPSocket()
    fake_thread = Mock()

    monkeypatch.setattr(
        "carcassonne.business_logic.client.socket.socket",
        lambda *args, **kwargs: fake_socket,
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.client.threading.Thread",
        lambda *args, **kwargs: fake_thread,
    )
    sent_messages = []
    client.send_to_server = lambda text: sent_messages.append(text) or True

    assert client.join_server() is True
    assert fake_socket.connected == (server_service.server_name, 4242)
    assert sent_messages == ["username=alice-remote password=pw"]


def test_receive_loop_processes_messages_and_handles_shutdown(monkeypatch, capsys) -> None:
    client, _, _ = build_client()
    handled = []

    class ReceiveSocket:
        def __init__(self, messages):
            self.messages = list(messages)
            self.closed = False

        def settimeout(self, value):
            self.timeout = value

        def recv(self, size):
            item = self.messages.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        def close(self):
            self.closed = True

    receive_socket = ReceiveSocket(
        [
            b"Server -> Client1: hello",
            b"Server -> Client1: Server Shutdown\n",
        ]
    )
    client.client = receive_socket
    client.has_joined_server = True
    client.handle_server_message = lambda message, server: handled.append(
        (message, server))
    client._receive_loop("srv")

    assert handled == [("Server -> Client1: hello", "srv")]
    assert receive_socket.closed is True
    captured = capsys.readouterr()
    assert "Server closed the connection." in (captured.out + captured.err)

    error_socket = ReceiveSocket([OSError("broken")])
    client.client = error_socket
    client._receive_loop("srv")
    captured = capsys.readouterr()
    assert "Socket error: broken" in (captured.out + captured.err)


def test_receive_loop_handles_timeouts_state_changes_and_close_errors(
    monkeypatch, capsys
) -> None:
    client, _, _ = build_client()

    class ReceiveSocket:
        def __init__(self):
            self.messages = [socket.timeout("wait"), b"Server -> Client1: ok"]
            self.closed = False

        def settimeout(self, value):
            self.timeout = value

        def recv(self, size):
            item = self.messages.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

        def close(self):
            self.closed = True
            raise RuntimeError("close fail")

    import socket

    receive_socket = ReceiveSocket()
    client.client = receive_socket
    client.has_joined_server = True

    def handle_message(message, server):
        with client.state_lock:
            client.has_joined_server = False

    client.handle_server_message = handle_message
    client._receive_loop("srv")

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "Error closing client socket: close fail" in output
    assert receive_socket.closed is True
    assert client.client is None


def test_handle_server_message_covers_board_request_registration_retry_and_visitor(
    monkeypatch, capsys
) -> None:
    client, repo, _ = build_client()
    client.client = object()
    sent = []
    client.send_to_server = lambda text: sent.append(text) or True
    visitor = Mock()
    client.register_message_visitor(visitor)

    client.handle_server_message("not-a-server-message", "srv")
    assert sent == []

    client.handle_server_message(
        "Server -> Client1: OPPONENT_MOVE did something", "srv"
    )
    assert sent == ["board"]

    with patch("builtins.input", side_effect=["y", "newname"]):
        client.handle_server_message(
            "Server -> Client1: Your registration has failed...",
            "srv",
        )
    assert client.temporary_username == "newname"
    assert sent[-1] == "username=newname password=pw\n"

    client.handle_server_message(
        "Server -> Client1: Successfull registering !",
        "srv",
    )
    repo.set_new_username_for_server.assert_called_once_with("srv", "newname")
    assert client.temporary_username == ""
    visitor.visit_server_message.assert_called()
    captured = capsys.readouterr()
    assert "OPPONENT_MOVE did something" in (captured.out + captured.err)


def test_handle_server_message_ignores_invalid_messages_and_declined_rename(
    capsys,
) -> None:
    client, _, _ = build_client()
    client.client = object()
    client.send_to_server = Mock()

    client.handle_server_message("bad-format", "srv")

    with patch("builtins.input", side_effect=["n"]):
        client.handle_server_message(
            "Server -> Client1: Your registration has failed...",
            "srv",
        )

    captured = capsys.readouterr()
    assert "Your registration has failed..." in (captured.out + captured.err)


def test_list_available_servers_and_timeout_cleanup_cover_valid_and_invalid_messages(
    monkeypatch, capsys
) -> None:
    client, _, _ = build_client()
    udp_socket = FakeUDPSocket(
        messages=[
            (b"127.0.0.1:4242", ("127.0.0.1", 12346)),
            (b"bad-port:notanint", ("127.0.0.1", 12346)),
        ]
    )
    times = iter([0.0, 0.0, 0.0, 1.0, 1.0, 2.0, 2.0, 6.0, 6.0, 6.0])

    monkeypatch.setattr(
        "carcassonne.business_logic.client.socket.socket",
        lambda *args, **kwargs: udp_socket,
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.client.select.select",
        lambda *args, **kwargs: ([udp_socket], [], []
                                 ) if udp_socket.messages else ([], [], []),
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.client.time.time",
        lambda: next(times),
    )

    servers = client.list_available_servers(timeout=5.0)

    assert servers == {"127.0.0.1": 4242}
    captured = capsys.readouterr()
    assert "Invalid port in message: bad-port:notanint" in (
        captured.out + captured.err)

    client.available_servers = {
        "old": (1111, 0.0),
        "new": (2222, 100.0),
    }
    monkeypatch.setattr(
        "carcassonne.business_logic.client.time.time",
        lambda: 129.0,
    )
    assert client.check_servers_last_time_sent() == {"new": (2222, 100.0)}

    client, _, _ = build_client()
    bad_socket = FakeUDPSocket(bind_error=OSError("bind failed"))
    monkeypatch.setattr(
        "carcassonne.business_logic.client.socket.socket",
        lambda *args, **kwargs: bad_socket,
    )
    client.list_available_servers(timeout=0.1)
    captured = capsys.readouterr()
    assert "Error binding socket: bind failed" in (captured.out + captured.err)


def test_list_available_servers_handles_invalid_format_and_receive_errors(
    monkeypatch, capsys
) -> None:
    client, _, _ = build_client()
    udp_socket = FakeUDPSocket(
        messages=[(b"invalid-message", ("127.0.0.1", 1))])
    times = iter([0.0, 0.0, 0.0, 1.0, 1.0, 6.0])

    monkeypatch.setattr(
        "carcassonne.business_logic.client.socket.socket",
        lambda *args, **kwargs: udp_socket,
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.client.select.select",
        lambda *args, **kwargs: ([udp_socket], [], []),
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.client.time.time",
        lambda: next(times),
    )

    assert client.list_available_servers(timeout=5.0) == {}
    captured = capsys.readouterr()
    assert "Invalid message format: invalid-message" in (
        captured.out + captured.err)

    client, _, _ = build_client()
    failing_udp_socket = FakeUDPSocket()

    def raise_recvfrom(size):
        raise RuntimeError("recv fail")

    failing_udp_socket.recvfrom = raise_recvfrom
    monkeypatch.setattr(
        "carcassonne.business_logic.client.socket.socket",
        lambda *args, **kwargs: failing_udp_socket,
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.client.select.select",
        lambda *args, **kwargs: ([failing_udp_socket], [], []),
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.client.time.time",
        lambda: 0.0,
    )

    assert client.list_available_servers(timeout=0.1) == {}
    captured = capsys.readouterr()
    assert "Error receiving message: recv fail" in (
        captured.out + captured.err)


def test_create_player_ping_connection_send_disconnect_and_visitor_registration(
    monkeypatch, capsys
) -> None:
    client, repo, server_service = build_client()
    assert client.create_default_online_player(
        " Bob ", "pw", "srv") == "created"
    assert client.client_player == "Bob"

    # Test send_to_server with no connection
    client.client = None
    assert client.connected_to_a_server() is False
    assert client.send_to_server("test") is False
    captured = capsys.readouterr()
    # The "Not connected to any server." message is printed to stdout
    output = captured.out + captured.err
    assert "Not connected to any server." in output

    # Test normal send_to_server with connected socket
    client, repo, server_service = build_client()
    fake_socket = FakeTCPSocket()
    client.client = fake_socket
    client.has_joined_server = True
    client.connected_server = "srv"
    repo.has_no_special_username.return_value = True
    assert client.send_to_server("test message") is True
    assert fake_socket.sent[-1] == b"alice: test message"
    assert client.connected_to_a_server() is True

    # Test disconnect
    recv_thread = Mock()
    recv_thread.is_alive.side_effect = [True, False]
    client._recv_thread = recv_thread
    client.available_servers = {"srv": (1, 1.0)}
    client.client = FakeTCPSocket()
    client.disconnect()
    assert client.available_servers == {}
    assert client.connected_server == ""
    assert client.shutdown_event.is_set() is True
    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "Client disconnection complete." in output

    # Test visitor registration
    visitor = Mock()
    client.register_message_visitor(visitor)
    assert client.message_visitor is visitor


def test_ping_send_to_server_and_disconnect_cover_remaining_branches(
    monkeypatch, capsys
) -> None:
    client, repo, _ = build_client()
    repo.has_no_special_username.return_value = False
    repo.get_online_player.side_effect = lambda server: {"srv": "alice-srv"}[
        server
    ]
    weird_socket = FakeTCPSocket()
    weird_socket.sendall = Mock(side_effect=RuntimeError("weird"))
    client.client = weird_socket
    client.has_joined_server = True
    client.connected_server = "srv"

    # Test sending with error
    assert client.send_to_server("hello") is False
    captured = capsys.readouterr()
    assert "Failed to send: weird" in (captured.out + captured.err)

    # Test disconnect with broken socket
    client, _, _ = build_client()
    broken_socket = FakeTCPSocket()
    broken_socket.shutdown = Mock(side_effect=OSError("shutdown failed"))
    client.client = broken_socket
    client.has_joined_server = True
    client.connected_server = "srv"
    recv_thread = Mock()
    recv_thread.is_alive.return_value = True
    client._recv_thread = recv_thread
    client.disconnect()

    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "Warning: receive thread did not terminate within timeout." in output
