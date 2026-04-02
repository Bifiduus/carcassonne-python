import select
import socket
import threading
import time

from carcassonne.business_logic.server import Server
from carcassonne.business_logic.interfaces.i_games_repository import (
    IGamesRepository,
)
from carcassonne.i18n import gettext as _
from carcassonne.presentation.interfaces.i_client_service import IClientService
from carcassonne.presentation.interfaces.i_client_message_visitor import (
    IClientMessageVisitor,
)


class Client(IClientService):

    # circulaire entre client et server, client avant server

    SERVER_TIMEOUT = 30

    def __init__(self, repo: IGamesRepository, server_service: Server):
        # client state
        self.client = None
        self.client_player = None
        self.has_joined_server = False
        self.available_servers: dict[str, tuple[int, float]] = {}
        self.temporary_username = ""
        self.client_id = None
        self.connected_server = ""
        self.repo = repo
        self.server_service = server_service
        self.server_name = server_service.server_name
        self._recv_thread = None
        self.shutdown_event = threading.Event()

        # Thread-safety locks
        # Protects: has_joined_server, client_id, connected_server
        self.state_lock = threading.Lock()
        self.servers_lock = threading.Lock()  # Protects: available_servers

        self.message_visitor: IClientMessageVisitor | None = None

        # Registering phase
        if not self.repo.is_accounted_for():
            print(_("You should create an online account.") + "\n")
            username = input(_(">> Your username is: "))
            password = input(_(">> Your password is: "))
            self.create_default_online_player(
                username, password, self.server_name
            )
        else:
            self.client_player = self.repo.get_online_player(self.server_name)

    # Client side
    def join_server(
        self,
        ip: str | None = None,
        port: int | None = None,
        timeout: float = 5.0,
    ) -> bool:
        """
        Connect to a remote server identified by name (and optional port).

        - If port is None, the method looks up the port from
          `available_servers` which is populated by `list_available_servers`.
        - Returns True if the connection is successfully established.
        - Once connected a background thread is started to receive messages
          from the server and dispatch them to `handle_server_message`.
        """
        if ip is None or ip == "":
            ip = self.server_service.server_name
        if ip not in self.available_servers:
            print(_("Error: there is no server with that IP address."))
            return False
        server_port = self.available_servers[ip][0]

        if port is None:
            port = server_port

        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(timeout)
        try:
            self.client.connect((ip, port))
            with self.state_lock:
                self.connected_server = ip
        except Exception as e:
            print(
                ("Unable to connect to {ip}:{port} -> {error}").format(
                    ip=ip,
                    port=port,
                    error=e,
                )
            )
            self.client.close()
            self.client = None
            return False

        # clear the timeout for normal operation
        self.client.settimeout(None)

        # send useful informations to the server
        username = ""

        if self.repo.has_no_special_username(ip):
            username = self.repo.get_online_player(
                self.server_service.server_name
            )

        else:
            username = self.repo.get_online_player(ip)
        information = (
            f"username={username} " f"password={self.repo.get_password(1)}"
        )

        self.send_to_server(information)

        # start a listener thread so the caller can interact without blocking
        self._recv_thread = threading.Thread(
            target=self._receive_loop, args=(ip,), daemon=True
        )
        self._recv_thread.start()
        with self.state_lock:
            self.has_joined_server = True
        return True

    def _receive_loop(self, server: str):
        """
        Internal helper that runs in a thread to read data from the server and
        dispatch it to `handle_server_message`.
        """
        try:
            assert self.client is not None, ""\
                "Client socket should be initialized"
            # Set a timeout for recv to allow periodic checks
            self.client.settimeout(1.0)
            while self.client and not self.shutdown_event.is_set():
                try:
                    data = self.client.recv(1500)
                    if not data:
                        break  # Connection closed by server
                    if data.decode().endswith("Server Shutdown\n"):
                        print(_("Server closed the connection."))
                        break
                    self.handle_server_message(data.decode(), server)
                    with self.state_lock:
                        if not self.has_joined_server:
                            break
                except socket.timeout:
                    continue  # Check for shutdown_event and loop again
                except OSError as e:
                    print(_("Socket error: {error}").format(error=e))
                    continue
        except Exception as e:
            print(_("Error receiving from server: {error}").format(error=e))
        finally:
            if self.client:
                try:
                    self.client.close()
                except Exception as e:
                    print(
                        _("Error closing client socket: {error}").format(
                            error=e
                        )
                    )
            self.client = None

    def handle_server_message(self, message: str, server: str):
        """
        Override or extend this method to process messages received from the
        server.
        """
        assert self.repo is not None, "No games repository."
        if self.client:
            message_content = message
            if message.find("Server ->") == -1:
                return
            message_content = message.removeprefix("Server -> ")
            client_id, message_content = message_content.split(":", 1)
            client_id = client_id.removeprefix("Client").strip()
            message_content = message_content.strip()
            print()
            print(message_content)
            if message_content.startswith("OPPONENT_MOVE"):
                self.send_to_server("board")

            # not own server
            if message_content == "Your registration has failed...":
                answer = input(
                    _("Would you like to try another username? (y/n)\n>> ")
                )
                if answer.lower() == "y":
                    username = input(_("username:\n>> "))
                    self.temporary_username = username
                    msg = f"username={username} password="\
                        f"{self.repo.get_password(1)}\n"
                    self.send_to_server(msg)
            if (message_content == "Successfull registering !" and
                    self.temporary_username != ""):
                self.repo.set_new_username_for_server(
                    server, self.temporary_username
                )
                self.temporary_username = ""

        # Notify any GUI visitor about incoming server message
        if self.message_visitor is not None:
            self.message_visitor.visit_server_message(message, server)

    def list_available_servers(self, timeout: float = 5.0) -> dict[str, int]:
        """
        Listen for available servers via UDP broadcasts for a specified
          timeout period.
        Returns a list of server names that responded within the timeout.
        """
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.bind(("", 12346))
            s.settimeout(timeout)  # Set socket timeout
        except Exception as e:
            print(_("Error binding socket: {error}").format(error=e))
            return {}

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                ready = select.select(
                    [s], [], [], timeout - (time.time() - start_time)
                )
                if ready[0]:
                    message, addr = s.recvfrom(1500)
                    message_part = message.decode()
                    if ":" in message_part:
                        ip, port_str = message_part.split(":", 1)
                        try:
                            port = int(port_str)
                            with self.servers_lock:
                                self.available_servers[ip] = (
                                    port, time.time())
                        except ValueError:
                            print(
                                _("Invalid port in message: {message}").format(
                                    message=message_part
                                )
                            )
                    else:
                        print(
                            _("Invalid message format: {message}").format(
                                message=message_part
                            )
                        )
                else:
                    break  # Timeout reached
            except socket.timeout:
                break
            except Exception as e:
                print(_("Error receiving message: {error}").format(error=e))
                break

        s.close()
        self.check_servers_last_time_sent()
        with self.servers_lock:
            available_servers: dict[str, int] = {}
            for server in self.available_servers:
                available_servers[server] = self.available_servers[server][0]
        return available_servers

    def check_servers_last_time_sent(self):
        """
        Remove servers from available_servers if they haven't sent a message
        within SERVER_TIMEOUT seconds.
        """
        with self.servers_lock:
            current_time = time.time()
            to_remove = []
            for name, (port, last_time) in self.available_servers.items():
                if current_time - last_time >= self.SERVER_TIMEOUT:
                    to_remove.append(name)
            for name in to_remove:
                del self.available_servers[name]
            return self.available_servers

    def create_default_online_player(
        self, username: str, password: str, server: str = "127.0.1.1"
    ) -> str:
        self.client_player = username.strip()
        assert self.repo, "The database should not be None"
        return self.repo.create_default_online_player(
            username, password, server
        )

    def ping(self) -> str:
        """
        Send a ping or check server status.
        Placeholder implementation.
        """
        start = time.time()
        self.send_to_server("ping")
        if self.client is None:
            return _("Error: no client socket found.")
        data = self.client.recv(1500)
        message = data.decode()
        if message.find("pong\n") != -1:
            end = time.time()
            return f"pong\nTime={end - start}ms"

        return _("No server response")  # Or implement actual ping logic

    def connected_to_a_server(self) -> bool:
        with self.state_lock:
            return bool(self.client and self.has_joined_server)

    def send_to_server(self, text: str) -> bool:
        """
        Send a message to the connected server. Returns False if not
        connected.
        """
        if not self.client:
            print(_("Not connected to any server."))
            return False
        try:
            with self.state_lock:
                if self.client_id is None:
                    assert self.repo, "The database should not be None"
                    self.client_id = self.repo.get_next_available_id()
                ip = self.connected_server

            if self.repo.has_no_special_username(ip):
                username = self.repo.get_online_player(
                    self.server_service.server_name
                )
            else:
                username = self.repo.get_online_player(ip)

            if text == "quit":
                with self.state_lock:
                    self.has_joined_server = False
            text = f"{username}: " + text
            self.client.sendall(text.encode())
            return True
        except (BrokenPipeError, ConnectionResetError, OSError) as e:
            # Socket is broken, likely during shutdown
            if "quit" not in str(text).lower():
                print(f"Failed to send: {e}")
            return False
        except Exception as e:
            print(_("Failed to send: {error}").format(error=e))
            return False

    def disconnect(self):
        """
        Disconnect from the server gracefully with proper resource cleanup.
        This handles both normal and forceful shutdowns.
        """
        print(_("Starting client disconnection..."))

        try:
            # 1. Try to send disconnect message (but don't fail if socket is broken)
            try:
                if self.client and self.connected_to_a_server():
                    self.send_to_server("Bad client disconnection\n")
            except (BrokenPipeError, OSError, ConnectionResetError):
                # Socket already broken, just continue with cleanup
                pass

            # 2. Signal the receive loop to stop
            with self.state_lock:
                self.has_joined_server = False
            self.shutdown_event.set()

            # 3. Close the client socket
            if self.client:
                try:
                    self.client.shutdown(socket.SHUT_RDWR)
                except Exception as e:
                    print(
                        _("Error closing client socket: {error}").format(
                            error=e
                        )
                    )
                self.client = None

            # 4. Wait for receive thread to finish (with timeout)
            if self._recv_thread and self._recv_thread.is_alive():
                try:
                    self._recv_thread.join(timeout=3.0)
                    if self._recv_thread.is_alive():
                        print(
                            _(
                                "Warning: receive thread did not terminate "
                                "within timeout."
                            )
                        )
                except Exception as e:
                    print(
                        _("Error joining receive thread: {error}").format(
                            error=e
                        )
                    )

            # 5. Clear available servers
            with self.servers_lock:
                self.available_servers.clear()

            # 6. Reset connection state
            with self.state_lock:
                self.temporary_username = ""
                self.connected_server = ""

            print(_("Client disconnection complete."))
        except Exception as e:
            print(f"Error during client disconnection: {e}")

    def register_message_visitor(
        self, visitor: IClientMessageVisitor
    ) -> None:
        """Register observer/visitor for incoming server messages."""
        self.message_visitor = visitor
