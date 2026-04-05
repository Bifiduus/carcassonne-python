from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

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
    def __init__(self, connect_error=None) -> None:
        self.connect_error = connect_error
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
    assert "there is no server with that IP address" in capsys.readouterr().out

    client.available_servers = {"10.0.0.1": (4242, 0.0)}
    fake_socket = FakeTCPSocket()
    fake_thread = Mock()
    monkeypatch.setattr("carcassonne.business_logic.client.socket.socket", lambda *args, **kwargs: fake_socket)
    monkeypatch.setattr("carcassonne.business_logic.client.threading.Thread", lambda *args, **kwargs: fake_thread)
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
    monkeypatch.setattr("carcassonne.business_logic.client.socket.socket", lambda *args, **kwargs: error_socket)

    assert client.join_server("10.0.0.1") is False
    assert client.client is None
    assert "Unable to connect to 10.0.0.1:4242" in capsys.readouterr().out


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
    client.handle_server_message = lambda message, server: handled.append((message, server))
    client._receive_loop("srv")

    assert handled == [("Server -> Client1: hello", "srv")]
    assert receive_socket.closed is True
    assert "Server closed the connection." in capsys.readouterr().out

    error_socket = ReceiveSocket([OSError("broken")])
    client.client = error_socket
    client._receive_loop("srv")
    assert "Socket error: broken" in capsys.readouterr().out


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
    assert "OPPONENT_MOVE did something" in capsys.readouterr().out


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
        lambda *args, **kwargs: ([udp_socket], [], []) if udp_socket.messages else ([], [], []),
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.client.time.time",
        lambda: next(times),
    )

    servers = client.list_available_servers(timeout=5.0)

    assert servers == {"127.0.0.1": 4242}
    assert "Invalid port in message: bad-port:notanint" in capsys.readouterr().out

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
    assert client.list_available_servers() == {}
    assert "Error binding socket: bind failed" in capsys.readouterr().out


def test_create_player_ping_connection_send_disconnect_and_visitor_registration(
    monkeypatch, capsys
) -> None:
    client, repo, server_service = build_client()
    assert client.create_default_online_player(" Bob ", "pw", "srv") == "created"
    assert client.client_player == "Bob"

    client.client = None
    client.send_to_server = Mock()
    assert client.ping() == "Error: no client socket found."

    client, repo, server_service = build_client()
    fake_socket = FakeTCPSocket()
    client.client = fake_socket
    client.has_joined_server = True
    client.connected_server = "srv"
    repo.has_no_special_username.return_value = True
    assert client.send_to_server("ping") is True
    assert fake_socket.sent[-1] == b"alice: ping"
    assert client.connected_to_a_server() is True

    fake_socket.recv = lambda size: b"pong\n"
    response = client.ping()
    assert response.startswith("pong\nTime=")

    client.client = None
    assert client.connected_to_a_server() is False
    assert client.send_to_server("test") is False
    assert "Not connected to any server." in capsys.readouterr().out

    broken_socket = FakeTCPSocket()
    broken_socket.sendall = Mock(side_effect=BrokenPipeError("broken"))
    client.client = broken_socket
    client.has_joined_server = True
    client.connected_server = "srv"
    assert client.send_to_server("hello") is False

    recv_thread = Mock()
    recv_thread.is_alive.side_effect = [True, False]
    client._recv_thread = recv_thread
    client.available_servers = {"srv": (1, 1.0)}
    client.client = FakeTCPSocket()
    client.disconnect()
    assert client.available_servers == {}
    assert client.connected_server == ""
    assert client.shutdown_event.is_set() is True
    assert "Client disconnection complete." in capsys.readouterr().out

    visitor = Mock()
    client.register_message_visitor(visitor)
    assert client.message_visitor is visitor
