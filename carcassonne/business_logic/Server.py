import sys
import time
import socket
import select
import threading

from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData
from carcassonne.BusinessLogic.OnlineCommunication import OnlineCommunication
from carcassonne.BusinessLogic.Player import Player
from carcassonne.BusinessLogic.Game import Game
from carcassonne.Datas.GraphData import GraphData
from carcassonne.Datas.GamesRepository import GameRepository
from carcassonne.BusinessLogic.Interfaces.IGamesRepository import IGamesRepository
from carcassonne.Presentation.Interfaces.IServerService import IServerService

# players_id de client_socket <-> db <-> id de players_clients | Unique par serveur


class Server(IServerService):
    SERVER_TIMEOUT = 30
    SERVER_DIFFUSION_PERIOD = 10
    INVITATION_TIMEOUT = 300

    def __init__(self, repo: IGamesRepository | None = None):
        # networking/server state
        self.server_name = ""
        self.client = None
        self.server = None
        self.running = False
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
        self.client_id = None
        # repository for persistence
        self.repo = repo if repo is not None else GameRepository()
        self.handle_communication = OnlineCommunication(self)

    def list_available_servers(self, timeout: float = 5.0) -> list[str]:
        """
        Listen for available servers via UDP broadcasts for a specified timeout period.
        Returns a list of server names that responded within the timeout.
        """
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        try:
            s.bind(('', 12346))
            s.settimeout(timeout)  # Set socket timeout
        except Exception as e:
            print(f"Error binding socket: {e}")
            return []

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
        return list(self.available_servers.keys())

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

    def server_start(self, port: int = 12345):
        """
        Start the TCP server on the specified port.
        Handles multiple clients concurrently using threading.
        """

        self.server = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind(('', port))
            self.server.listen(5)  # Allow up to 5 pending connections
            print(f"Server started on port {port}")
        except Exception as e:
            print(f"Error starting server: {e}")
            return

        self.running = True
        server_last_diffusion = time.time()
        while self.running:
            try:
                # Timeout to check self.running periodically
                self.server.settimeout(1.0)
                client_socket, addr = self.server.accept()
                print(f"Accepted connection from {addr}")
                # Add client to the list
                with self.clients_lock:
                    self.connected_clients.append(client_socket)
                # Handle client in a new thread
                client_thread = threading.Thread(
                    target=self.handle_client, args=(client_socket,))
                client_thread.start()

                # Timeout to check pending invitations periodically
                self.repo.check_all_invitations_timeout(
                    self.INVITATION_TIMEOUT)

                if time.time() - server_last_diffusion >= self.SERVER_DIFFUSION_PERIOD:
                    message = f"{self.server_name}:{port}"
                    socket_message = socket.socket(
                        socket.AF_INET, socket.SOCK_DGRAM)
                    socket_message.setsockopt(
                        socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    broadcast_addr = ('', 12346)
                    socket_message.sendto(message.encode(), broadcast_addr)
                    socket_message.close()
            except socket.timeout:
                continue  # Check self.running again
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
                break

        self.server.close()
        print("Server stopped")

    def handle_client(self, client_socket: socket.socket):
        """
        Handle communication with a single client.
        """

        try:
            while True:
                data = client_socket.recv(1500)
                if data.decode() == "quit\n":
                    break
                # Process data (e.g., echo back for now; replace with game logic)
                client, message = data.decode().split(":")
                client_id = client.removeprefix("Client")
                response = self.process_message(client_id, message)
                # fonction qui check le statut d'une invitation et l'envoie à l'host
                client_socket.send(
                    (f"Server -> Client{self.connected_clients.index(client_socket)}: " + response).encode())
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

    def process_message(self, client_id: str, message: str) -> str:
        """
        Process incoming message (from a client) and return a response.
        """
        # TODO: Integrate with game logic, e.g., handle moves, queries
        answer = ""
        if self.server is not None:
            if message == "ping\n":
                answer = self.handle_communication.command_ping()
            if message == "quit\n":
                answer = self.handle_communication.command_quit(client_id)
            if message == "server status\n":
                answer = self.handle_communication.command_server_status()
            if message.startswith("new"):
                answer = self.handle_communication.command_new(
                    message, client_id)
            if message == "players":
                answer = self.handle_communication.command_players(message)
            if message == "scoreboard\n":
                answer = self.handle_communication.command_scoreboard()
            if message == "accept\n":
                answer = self.handle_communication.command_accept(client_id)
            if message == "decline\n":
                answer = self.handle_communication.command_decline(client_id)
            if message.startswith("cancel"):
                answer = self.handle_communication.command_cancel(
                    client_id, message.strip("cancel"))
            if message == "away\n":
                answer = self.handle_communication.command_away(client_id)
            if message == "back\n":
                answer = self.handle_communication.command_back(client_id)
        return answer

    def check_clients_list_validity(self, clients_list: list[str]) -> list[str]:
        """Verify that each client id refers to an existing player via the repository."""
        assert self.repo is not None, "No games repository."
        return [c for c in clients_list if self.repo.player_exists(c)]

    def create_new_party(self, clients_list: list[str], host_id: int,  party_name: str = "") -> str:
        assert self.repo is not None, "No games repository."
        if party_name is "":
            party_name = self.repo.get_party_name(host_id)

        # should be done after, because don't know how many
        number_of_players_in_group: int = len(clients_list)
        graph: IGraphData = GraphData()
        new_party = Game(graph, number_of_players_in_group)
        try:
            self.repo.create_party(party_name, clients_list, host_id)
            self.current_games_list[len(self.current_games_list)] = (
                party_name, new_party)
            players_list = self.create_players_from_list(clients_list)
            new_party.start_online_game(players_list)
            # création approfondit de la game ( new method avec données de repo (groups et players ) )
        except Exception as e:
            print(f"Error creating party in repository: {e}")
        return "Your party has been created successfully !\n"

    def create_players_from_list(self, clients_list: list[str]) -> list[Player]:
        players_list = []
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
        return (
            f"{profile['username']} status={profile['status']} score={profile['score']} "
            f"wins={profile['stats_win']} loses={profile['stats_lose']}\n"
        )

    def send_invitation(self, invited_player: str, invitee_player: str):
        invited_client: socket.socket = self.client_sockets[int(
            invited_player)]
        message = f"Server: You have received an invitation from {self.repo.get_username(invitee_player)}.\n"
        message += f"Expires in 300s.\n"
        with self.clients_lock:
            try:
                invited_client.sendall(message.encode())
                self.repo.send_invitation(invited_player, invitee_player)
            except Exception as e:
                print(f"Error sending invitation: {e}")

    def server_stop(self):
        """
        Stop the server gracefully.
        """
        self.running = False
        # Send shutdown message to all connected clients
        shutdown_message = "Server Shutdown"
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
            self.server.close()
        # close repository database connection if there is one
        if hasattr(self, 'repo') and self.repo:
            try:
                self.repo.close()
            except Exception:
                pass

    def server_quit(self):
        """
        Quit the server and clean up resources.
        """
        if self.client == None:
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
        self.send_to_server("ping\n")
        if self.client == None:
            return "Error: no client socket found."
        data = self.client.recv(1500)
        message = data.decode()
        if message.find("pong\n") != -1:
            end = time.time()
            return message+f" Time={start - end}ms"

        return "No server response"  # Or implement actual ping logic

    def join_server(self, ip: str | None = None, port: int | None = None, timeout: float = 5.0) -> bool:
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

        if ip not in self.available_servers:
            print("Error: There is no server with such an ip.")
            return False
        if ip is None:
            ip = "localhost"
        server_port, _ = self.available_servers[ip]
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

        # start a listener thread so the caller can interact without blocking
        self._recv_thread = threading.Thread(
            target=self._receive_loop, daemon=True)
        self._recv_thread.start()
        return True

    def _receive_loop(self):
        """
        Internal helper that runs in a thread to read data from the server and
        dispatch it to `handle_server_message`.
        """
        try:
            while self.client:
                data = self.client.recv(1500)
                if not data or data.decode('utf-8') == "Server Shutdown\n":
                    print("Server closed the connection")
                    break
                self.handle_server_message(data.decode())
        except Exception as e:
            print(f"Error receiving from server: {e}")
        finally:
            if self.client:
                self.client.close()
            self.client = None

    def handle_server_message(self, message: str):
        """
        Override or extend this method to process messages received from the
        server.
        """
        assert self.repo is not None, "No games repository."
        if self.client:  # check what you do, if you have the server or if you only receive
            message = message.removeprefix("Server -> Client")
            client_id, message = message.split(":")
            if message.startswith("OPPONENT_MOVE"):
                move = message.split("OPPONENT_MOVE")
                # will check in the database for the game id and
                self.get_game(client_id).play_move(move[1])
                self.client.sendall("board".encode())  # pour afficher le coup
            if message.startswith("INVITATION_ACCEPTED"):
                # accepted or not or timed_out
                if self.repo.check_all_invitations_resolved(int(client_id)):
                    # ajoute la party dans party_list, change ce qu'il faut et lance
                    self.create_new_party(
                        self.repo.get_party(client_id), int(client_id))

        print(message, end="")

    def get_game(self, client_id: str):
        assert self.repo is not None, "No games repository."
        party_id = int(self.repo.get_game(int(client_id))[0])
        return self.current_games_list[party_id][1]

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
                self.client_id = self.repo.get_next_available_id()
            text = f"Client{self.client_id}: " + text
            self.client.sendall(text.encode())
            return True
        except Exception as e:
            print(f"Failed to send: {e}")
            return False
