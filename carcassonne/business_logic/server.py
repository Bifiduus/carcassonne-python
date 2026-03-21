import time
import socket
import select
import threading

from carcassonne.business_logic.interfaces.i_graph_data import IGraphData
from carcassonne.business_logic.online_communication import OnlineCommunication
from carcassonne.business_logic.player import Player
from carcassonne.business_logic.game import Game
from carcassonne.datas.graph_data import GraphData
from carcassonne.datas.games_repository import GameRepository
from carcassonne.business_logic.interfaces.i_games_repository \
    import IGamesRepository
from carcassonne.presentation.interfaces.i_server_service import IServerService


class Server(IServerService):
    SERVER_TIMEOUT = 30
    SERVER_DIFFUSION_PERIOD = 10
    INVITATION_TIMEOUT = 300

    def __init__(self, repo: IGamesRepository | None = None):
        # networking/server state
        self.server_name = "local"
        self.client = None
        self.client_player = None
        self.temporary_username = ""
        self.server = None
        self.has_joined_server = False
        self.should_stop = threading.Event()
        self.server_thread = None
        self.available_servers: dict[str, tuple[int, float]] = {}
        # List to track connected client sockets
        self.connected_clients: list[socket.socket] = []
        self.clients_lock = threading.Lock()  # Lock for thread-safe access
        # Needed to keep track of the different games
        self.current_games_list: dict[int, tuple[str, Game]] = {}
        # Map client_id -> socket
        self.client_sockets: dict[int, socket.socket] = {}
        self.player_clients: dict[socket.socket,
                                  int] = {}  # Map socket -> client_id
        self.registered_clients: dict[int, bool] = {}
        self.client_id = None
        # repository for persistence
        self.repo = repo if repo is not None else GameRepository()
        assert self.repo, "The database should not be None"
        self.handle_communication = OnlineCommunication(self)
        if not self.repo.is_accounted_for():
            print(f"You should create an online account.\n")
            username = input(">> Your username is: ")
            password = input(">> Your password is: ")
            self.create_default_online_player(username, password)
        else:
            self.client_player = self.repo.get_online_player("default")

    def create_default_online_player(self, username: str, password: str) -> str:
        self.client_player = username
        assert self.repo, "The database should not be None"
        return self.repo.create_default_online_player(username, password)

    def list_available_servers(self, timeout: float = 5.0) -> dict[str, int]:
        """
        Listen for available servers via UDP broadcasts
        for a specified timeout period.
        Returns a list of server names that responded within the timeout.
        """
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        try:
            s.bind(('', 12346))
            s.settimeout(timeout)  # Set socket timeout
        except Exception as e:
            print(f"Error binding socket: {e}")
            return {}

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                ready = select.select(
                    [s], [], [], timeout - (time.time() - start_time))
                if ready[0]:
                    message, addr = s.recvfrom(1500)
                    message_part = message.decode()
                    if ":" in message_part:
                        ip, port_str = message_part.split(":", 1)
                        try:
                            port = int(port_str)
                            self.available_servers[ip] = (port, time.time())
                        except ValueError:
                            print(f"Invalid port in message: {message_part}")
                    else:
                        print(f"Invalid message format: {message_part}")
                else:
                    break  # Timeout reached
            except socket.timeout:
                break
            except Exception as e:
                print(f"Error receiving message: {e}")
                break

        s.close()
        self.check_servers_last_time_sent()
        available_servers: dict[str, int] = {}
        for server in self.available_servers:
            available_servers[server] = self.available_servers[server][0]
        return available_servers

    def check_servers_last_time_sent(self):
        """
        Remove servers from available_servers if they haven't sent a message
        within SERVER_TIMEOUT seconds.
        """
        current_time = time.time()
        to_remove = []
        for name, (port, last_time) in self.available_servers.items():
            if current_time - last_time >= self.SERVER_TIMEOUT:
                to_remove.append(name)
        for name in to_remove:
            del self.available_servers[name]
        return self.available_servers

    def server_start(self, port: str = "12345"):
        """
        Start the TCP server on the specified port.
        Handles multiple clients concurrently using threading.
        """
        assert self.repo, "The database should not be None"
        if self.repo.is_database_closed():
            self.repo.reopen()
        if port == "":
            port = "12345"
        self.server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind(('', int(port)))
            self.server.listen(5)  # Allow up to 5 pending connections
            print(f"Server started on port {port}")
        except Exception as e:
            print(f"Error starting server: {e}")
            return
        self.should_stop.set()
        self.server_thread = threading.Thread(
            target=self.server_running, args=(port,))
        self.server_thread.start()

    def server_running(self, port):
        assert self.server
        server_last_diffusion = time.time()
        while self.should_stop.is_set():
            try:
                # Timeout to check self.running periodically
                self.server.settimeout(1.0)
                r, _, _ = select.select([self.server], [], [], 1.0)
                for s in r:
                    if s is self.server:
                        client_socket, addr = self.server.accept()
                        # Add client to the list
                        with self.clients_lock:
                            self.connected_clients.append(client_socket)
                            id = len(self.client_sockets)
                            self.client_sockets[id] = client_socket
                            self.player_clients[client_socket] = id
                            self.registered_clients[id] = False
                        # Handle client in a new thread
                        client_thread = threading.Thread(
                            target=self.handle_client, args=(client_socket,))
                        client_thread.start()
                        print("Accepted connection from a client.")

                # Timeout to check pending invitations periodically
                assert self.repo, "The database should not be None"
                self.repo.check_all_invitations_timeout(
                    self.INVITATION_TIMEOUT)

                # Timeout to check pending invitations periodically
                self.repo.check_all_invitations_timeout(
                    self.INVITATION_TIMEOUT)
                diffusion_period = self.SERVER_DIFFUSION_PERIOD
                if time.time() - server_last_diffusion >= diffusion_period:
                    message = f"{socket.gethostbyname(socket.gethostname())}:"
                    f"{port}"
                    socket_message = socket.socket(
                        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                    socket_message.setsockopt(
                        socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    broadcast_addr = ('<broadcast>', 12346)
                    socket_message.sendto(message.encode(), broadcast_addr)
                    socket_message.close()
            except socket.timeout:
                continue  # Check self.running again
            except Exception as e:
                if self.should_stop.is_set():
                    print(f"Error accepting connection: {e}")
                break
        self.server.close()
        print("Server stopped")

    def is_server_running(self) -> bool:
        return self.should_stop.is_set()

    def client_is_registered(self, client_index: int) -> bool:
        return self.registered_clients[client_index]

    def handle_client(self, client_socket: socket.socket):
        """
        Handle communication with a single client.
        """

        try:
            while True:
                data = client_socket.recv(1500)
                if data.decode() == "":
                    continue
                client, message = data.decode().split(":")
                message = message.strip()
                client_index = self.connected_clients.index(client_socket)
                if self.client_is_registered(client_index):
                    if message == "quit":
                        answer = self.handle_communication.command_quit(
                            client)
                        answer = f"Server -> Client{client_index}: {answer}"
                        client_socket.send(answer.encode())
                        self.has_joined_server = False
                        break

                    # Process data (e.g., echo back for now; replace with game logic)

                    response = self.process_message(client, message)
                    # fonction qui check le statut d'une invitation et l'envoie à l'host
                    answer = f"Server -> Client{client_index}: {response}\n"
                    client_socket.send(answer.encode())
                else:
                    self.handle_client_registering(
                        message, client_socket, client_index)
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client_socket.close()
            # Remove client from the list
            with self.clients_lock:
                if client_socket in self.connected_clients:
                    self.connected_clients.remove(client_socket)
                if client_socket in self.player_clients:
                    client_id = self.player_clients[client_socket]
                    del self.client_sockets[client_id]
                    del self.player_clients[client_socket]
                    del self.registered_clients[client_id]

    def handle_client_registering(self, message: str, client_socket: socket.socket, client_index: int):
        """
        Process client registering and return a response.
        """
        preface = f"Server -> Client{client_index}: "
        if message.find("username=") == -1:
            answer = f"{preface}You should send your username and password !\n"
            answer += "Type: username=<your username> password=<your password>\n"
            answer += "If it is your first time connecting, you can create one.\n"
        else:
            if message.find("username=") != -1 and message.find("password=") != -1:
                start_password: int = message.find("password=")
                username: str = message.removeprefix(
                    "username=")[:start_password]
                password: str = message[start_password:]
                success = self.repo.registering(username, password)
                if success:
                    answer = f"{preface}Successfull registering !\n"
                    self.registered_clients[client_index] = True
                else:
                    answer = f"{preface}Your registration has failed...\n"
            else:
                answer = f"{preface}You should send your username and password !\n"
        client_socket.send(answer.encode())

    def check_username_taken(self, username: str):
        answer: bool = self.repo.player_exists(username)
        return answer

    def process_message(self, client_id: str, message: str) -> str:
        """
        Process incoming message (from a client) and return a response.
        """
        answer = ""
        if self.server is not None:
            if message == "ping":
                answer = self.handle_communication.command_ping()
            if message == "server status":
                answer = self.handle_communication.command_server_status()
            if message.startswith("new"):
                answer = self.handle_communication.command_new(
                    message, client_id)
            if message.startswith("players"):
                answer = self.handle_communication.command_players(message)
            if message.startswith("play"):
                answer = self.handle_communication.command_play(
                    message, client_id)
            if message == "scoreboard":
                answer = self.handle_communication.command_scoreboard()
            if message == "accept":
                answer = self.handle_communication.command_accept(
                    client_id)
            if message == "decline":
                answer = self.handle_communication.command_decline(
                    client_id)
            if message.startswith("cancel"):
                answer = self.handle_communication.command_cancel(
                    client_id, message.strip("cancel"))
            if message == "away":
                answer = self.handle_communication.command_away(
                    client_id)
            if message == "back":
                answer = self.handle_communication.command_back(
                    client_id)
        return answer

    def check_clients_list_validity(self,
                                    clients_list: list[str]) -> list[str]:
        """Verify that each client id refers to
          an existing player via the repository."""
        assert self.repo is not None, "No games repository."
        return [c for c in clients_list if
                self.repo.player_exists(self.repo.get_username(c))]

    def create_new_party(self, clients_list: list[str],
                         client_id: str,  party_name: str = "") -> str:
        assert self.repo is not None, "No games repository."
        if party_name == "":
            party_name = self.repo.get_party_name(client_id)

        # should be done after, because don't know how many
        number_of_players_in_group: int = len(clients_list)
        graph: IGraphData = GraphData()
        new_party = Game(graph, number_of_players_in_group)
        try:
            self.repo.create_party(party_name, clients_list, client_id)
            self.current_games_list[len(self.current_games_list)] = (
                party_name, new_party)
            players_list = self.create_players_from_list(clients_list)
            new_party.start_online_game(players_list)
        except Exception as e:
            print(f"Error creating party in repository: {e}")
        return "Your party has been created successfully !\n"

    def create_players_from_list(self,
                                 clients_list: list[str]) -> list[Player]:
        players_list = []
        assert self.repo, "The database should not be None"
        for client in clients_list:
            username = self.repo.get_username(client)
            players_list.append(Player(int(client), username, "None"))
        return players_list

    def check_profile_player(self, player_id: int) -> str:
        """Return a simple textual profile for the given player id."""
        assert self.repo is not None, "No games repository."
        profile = self.repo.get_player_profile(player_id)
        if profile is None:
            return "Player not found\n"
        return f"Player profile:\n username={profile['username']}\n"\
            "status={profile['status']}\n score={profile['score']}\n "\
            f"wins={profile['stats_win']}\n loses={profile['stats_lose']}\n"

    def send_invitation(self, invited_player_id: str, invitee_player_id: str):
        invited_client: socket.socket = self.client_sockets[int(
            invited_player_id)]
        host_name: str = self.repo.get_username(invitee_player_id)
        message = "Server: You have received an invitation"\
            f"from {host_name}.\n"
        message += "Expires in 300s.\n"
        with self.clients_lock:
            try:
                invited_client.sendall(message.encode())
                assert self.repo, "The database should not be None"
                self.repo.send_invitation(invited_player_id, invitee_player_id)
            except Exception as e:
                print(f"Error sending invitation: {e}")

    def server_stop(self):
        """
        Stop the server gracefully.
        """
        if self.server_thread is not None:

            # Send shutdown message to all connected clients
            shutdown_message = "Server Shutdown\n"
            with self.clients_lock:
                # Copy the list to avoid modification during iteration
                for client_socket in self.connected_clients[:]:
                    try:
                        client_socket.sendall(shutdown_message.encode())
                    except Exception as e:
                        print(f"Error sending shutdown message to client: {e}")
                    finally:
                        client_socket.close()
                self.connected_clients.clear()
            if self.server:
                self.should_stop.clear()
                self.server.close()
            # close repository database connection if there is one
            if hasattr(self, 'repo') and self.repo:
                try:
                    self.repo.close()
                except Exception:
                    pass
            self.server_thread.join()

    def server_quit(self):
        """
        Quit the server and clean up resources.
        """
        if self.client is None:
            print("Error: no client socket found.")
            return -1
        data = "quit\n".encode()
        self.client.sendall(data)
        self.server_stop()
        return 0
        # Additional cleanup if needed

    def ping(self) -> str:
        """
        Send a ping or check server status.
        Placeholder implementation.
        """
        start = time.time()
        self.send_to_server("ping")
        if self.client is None:
            return "Error: no client socket found."
        data = self.client.recv(1500)
        message = data.decode()
        if message.find("pong\n") != -1:
            end = time.time()
            return f"pong\nTime={end - start}ms"

        return "No server response"  # Or implement actual ping logic

    def join_server(self, ip: str | None = None,
                    port: int | None = None, timeout: float = 5.0) -> bool:
        """
        Connect to a remote server identified by name (and optional port).

        - If port is None, the method looks up the port from
          `available_servers` which is populated by `list_available_servers`.
        - Returns True if the connection is successfully established.
        - Once connected a background thread is started to receive messages
          from the server and dispatch them to `handle_server_message`.
        """
        # refresh discovery cache first
        self.list_available_servers()
        if ip is (None or ""):
            ip = self.server_name
        if ip not in self.available_servers:
            print("Error: There is no server with such an ip.")
            return False

        server_port, _ = self.available_servers[ip]
        self.connected_to_server_index = ip
        if port is None:
            port = server_port

        self.client = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.client.settimeout(timeout)
        try:
            self.client.connect((ip, port))
        except Exception as e:
            print(f"Unable to connect to {ip}:{port} -> {e}")
            self.client.close()
            self.client = None
            return False

        # clear the timeout for normal operation
        self.client.settimeout(None)

        # send useful informations to the server
        username = ""
        if self.repo.has_no_special_username(ip):
            username = self.repo.get_online_player("default")
        else:
            username = self.repo.get_online_player(ip)
        information = f"username={username} password={self.repo.get_password(0)}"
        self.send_to_server(information)

        # start a listener thread so the caller can interact without blocking
        self._recv_thread = threading.Thread(
            target=self._receive_loop, args=(ip,),  daemon=True)
        self._recv_thread.start()
        self.has_joined_server = True
        return True

    def _receive_loop(self, server: str):
        """
        Internal helper that runs in a thread to read data from the server and
        dispatch it to `handle_server_message`.
        """
        try:
            while self.client:
                data = self.client.recv(1500)
                if data.decode().endswith("Server Shutdown\n"):
                    print("Server closed the connection")
                    break
                self.handle_server_message(data.decode(), server)
                if (not self.has_joined_server):
                    break
        except Exception as e:
            print(f"Error receiving from server: {e}")
        finally:
            if self.client:
                self.client.close()
            self.client = None

    def handle_server_message(self, message: str, server: str):
        """
        Override or extend this method to process messages received from the
        server.
        """
        assert self.repo is not None, "No games repository."
        # check what you do, if you have the server or if you only receive
        if self.client:
            message = message.removeprefix("Server -> ")
            client_id, message = message.split(":", 1)
            client_id = client_id.removeprefix("Client").strip()
            message = message.strip()
            print(message, end="")
            if message.startswith("OPPONENT_MOVE"):
                move = message.split("OPPONENT_MOVE")
                # will check in the database for the game id and
                self.get_game(client_id).play_move(move[1])
                self.client.sendall("board".encode())  # pour afficher le coup
            if message.startswith("INVITATION_ACCEPTED"):
                # accepted or not or timed_out
                if self.repo.check_all_invitations_resolved(client_id):
                    # ajoute la party dans party_list,
                    #  change ce qu'il faut et lance
                    self.create_new_party(
                        self.repo.get_party(client_id), client_id)

            # not own server
            if message == "Your registration has failed...":
                username = input("You must send another username:\n>> ")
                self.temporary_username = username
                message = f"username={username} password={self.repo.get_password(0)}\n"
                self.send_to_server(message)
            if message == "Successfull registering !" and self.temporary_username != "":
                self.repo.set_new_username_for_server(
                    server, self.temporary_username)

    def get_game(self, client_id: str):
        assert self.repo is not None, "No games repository."
        party_id = int(self.repo.get_game(client_id))
        return self.current_games_list[party_id][1]

    def connected_to_a_server(self) -> bool:
        return bool(self.client and self.has_joined_server)

    def send_to_server(self, text: str) -> bool:
        """
        Send a message to the connected server. Returns False if not
        connected.
        """
        if not self.client:
            print("Not connected to any server")
            return False
        try:
            if self.client_id is None:
                assert self.repo, "The database should not be None"
                self.client_id = self.repo.get_next_available_id()
            text = f"{self.client_player}: " + text
            self.client.sendall(text.encode())
            return True
        except Exception as e:
            print(f"Failed to send: {e}")
            return False
