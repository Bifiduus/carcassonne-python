import sys
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
from carcassonne.business_logic.interfaces.i_games_repository import IGamesRepository
from carcassonne.presentation.interfaces.i_server_service import IServerService

# players_id de client_socket <-> db <-> id de players_clients | Unique par serveur


class Server(IServerService):
    SERVER_TIMEOUT = 30
    SERVER_DIFFUSION_PERIOD = 10
    INVITATION_TIMEOUT = 300

    def __init__(self, repo: IGamesRepository | None = None):
        # networking/server state
        self.server_name = socket.gethostbyname(socket.gethostname())
        self.server = None
        self.should_stop = threading.Event()
        self.server_thread = None
        # List to track connected client sockets
        self.connected_clients: list[socket.socket] = []
        self.clients_lock = threading.Lock()  # Lock for thread-safe access
        # Needed to keep track of the different games
        self.current_games_list: dict[int, tuple[str, Game]] = {}
        # Map client_username -> socket
        self.client_sockets: dict[str, socket.socket] = {}
        # Map socket -> client_username
        self.player_clients: dict[socket.socket, str] = {}
        self.registered_clients: dict[socket.socket, bool] = {}
        # repository for persistence
        self.repo = repo if repo is not None else GameRepository()
        assert self.repo, "The database should not be None"
        self.handle_communication = OnlineCommunication(self)

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
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind(('', int(port)))
            self.server.listen()
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
        first_diffusion = True
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
                            id = len(self.connected_clients)+1
                            self.registered_clients[client_socket] = False
                        # Handle client in a new thread
                        client_thread = threading.Thread(
                            target=self.handle_client, args=(client_socket,))
                        client_thread.start()
                        print(f"Accepted connection from a client.")

                # Timeout to check pending invitations periodically
                assert self.repo, "The database should not be None"
                self.repo.check_all_invitations_timeout(
                    self.INVITATION_TIMEOUT)

                # Determine if a party can be launched, and if so, do it
                self.launch_availables_games()

                # Determine if a party ended, and if so, clean it
                self.clean_finished_games()

                time_passed = time.time() - server_last_diffusion
                clock = self.SERVER_DIFFUSION_PERIOD
                if time_passed >= clock or first_diffusion:
                    server_last_diffusion = time.time()
                    host_name = socket.gethostname()
                    message = f"{socket.gethostbyname(host_name)}:{port}"
                    socket_message = socket.socket(
                        socket.AF_INET, socket.SOCK_DGRAM,
                        socket.IPPROTO_UDP)
                    socket_message.setsockopt(
                        socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    broadcast_addr = ('<broadcast>', 12346)
                    socket_message.sendto(message.encode(), broadcast_addr)
                    socket_message.close()
                    if first_diffusion:
                        first_diffusion = False

            except socket.timeout:
                continue  # Check self.running again
            except Exception as e:
                if self.should_stop.is_set():
                    print(f"Error accepting connection: {e}")
                break
        self.server.close()
        print("Server stopped")

    def launch_availables_games(self):
        # For all parties, check if game can be launched
        # If so launch it, and handle_party() ( like handle_client but for a game )
        for party in range(1, self.repo.get_parties() + 1):
            check = self.party_can_be_launched(party)
            # Check if players are ok for party to be launched
            if check:
                host_id: int = self.repo.get_host_from_party(party)
                players = self.repo.get_party(str(host_id))
                self.create_new_party(players, str(host_id))

    def party_can_be_launched(self, party_number: int) -> bool:
        host_id: int = self.repo.get_host_from_party(party_number)
        check = self.repo.check_all_invitations_resolved(str(host_id))
        return check

    def clean_finished_games(self):
        for party in range(1, self.repo.get_parties() + 1):
            check = self.party_is_finished(party)
            if check:
                self.repo.clean_party(party)
                host_id: int = self.repo.get_host_from_party(party)
                party_id = self.repo.get_party_id(str(host_id))
                assert party_id == party, "Error in creation of parties.."
                del self.current_games_list[party_id]

    def party_is_finished(self, party: int) -> bool:
        return self.current_games_list[party][1].end_game()

    def is_server_running(self) -> bool:
        return self.should_stop.is_set()

    def client_is_registered(self, client_socket: socket.socket) -> bool:
        return self.registered_clients[client_socket]

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
                client_index = self.repo.get_id_from_username(
                    client)
                if self.client_is_registered(client_socket):

                    if message == "quit":
                        answer = self.handle_communication.command_quit(
                            client)
                        answer = f"Server -> Client{client_index}: {answer}\n"
                        client_socket.send(answer.encode())
                        break

                    # Process data
                    response = self.process_message(str(client_index), message)
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
                    username = self.player_clients[client_socket]
                    del self.client_sockets[username]
                    del self.player_clients[client_socket]
                    del self.registered_clients[client_socket]

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
                username, password = message.split(" password=")
                username: str = username.removeprefix(
                    "username=")
                success = self.repo.registering(username, password)
                if success:
                    answer = f"{preface}\nSuccessfull registering !\n"
                    self.registered_clients[client_socket] = True
                    self.client_sockets[username] = client_socket
                    self.player_clients[client_socket] = username
                else:
                    answer = f"{preface}\nYour registration has failed...\n"
            else:
                answer = f"{preface}\nYou should send your username and password !\n"
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
            elif message == "server status":
                answer = self.handle_communication.command_server_status()
            elif message.startswith("new"):
                answer = self.handle_communication.command_new(
                    message, client_id)
            elif message.startswith("players"):
                answer = self.handle_communication.command_players(message)
            elif message.startswith("play"):
                answer = self.handle_communication.command_play(
                    message, client_id)
            elif message == "scoreboard":
                answer = self.handle_communication.command_scoreboard()
            elif message == "accept":
                answer = self.handle_communication.command_accept(
                    client_id)
            elif message == "decline":
                answer = self.handle_communication.command_decline(
                    client_id)
            elif message.startswith("cancel"):
                answer = self.handle_communication.command_cancel(
                    client_id, message.strip("cancel"))
            elif message == "away":
                answer = self.handle_communication.command_away(
                    client_id)
            elif message == "back":
                answer = self.handle_communication.command_back(
                    client_id)
            elif message.startswith("board"):
                answer = self.handle_communication.command_board(
                    client_id)
            elif message.startswith("set"):
                answer = self.handle_communication.command_set(
                    client_id, message)
            elif message == "show configuration":
                answer = self.handle_communication.command_config(
                    client_id)
            elif message == "show history":
                answer = self.handle_communication.command_history(
                    client_id)
            elif message == "show score":
                answer = self.handle_communication.command_score(
                    client_id)
            elif message == "show hand":
                answer = self.handle_communication.command_hand(
                    client_id)
            elif message == "redo":
                answer = self.handle_communication.command_redo(
                    client_id)
            elif message == "undo":
                answer = self.handle_communication.command_undo(
                    client_id)
            elif message == "hint":
                answer = self.handle_communication.command_hint(
                    client_id)
            elif message == "draw":
                answer = self.handle_communication.command_draw(
                    client_id)
            elif message == "shuffle":
                answer = self.handle_communication.command_shuffle(
                    client_id)
            elif message.startswith("save "):
                answer = self.handle_communication.command_save(
                    client_id, message)
            elif message.startswith("load "):
                answer = self.handle_communication.command_load(
                    client_id, message)
        return answer

    def check_clients_list_validity(self, clients_list: list[str]) -> list[str]:
        """Verify that each client id refers to an existing player via the repository."""
        assert self.repo is not None, "No games repository."
        return [c for c in clients_list if self.repo.player_exists(self.repo.get_username(c))]

    def create_new_party(self, clients_list: list[int], client_id: str,  party_name: str = "") -> str:
        assert self.repo is not None, "No games repository."
        party_id = self.repo.get_party_id(client_id)
        if party_name == "":
            party_name = f"Party {party_id}"

        # Initialize the game
        number_of_players_in_group: int = len(clients_list)
        graph: IGraphData = GraphData()
        new_party = Game(graph, number_of_players_in_group)
        try:
            self.current_games_list[party_id] = (
                party_name, new_party)
            players_list = self.create_players_from_list(clients_list)
            new_party.start_online_game(players_list)
        except Exception as e:
            print(f"Error creating party in repository: {e}")
        return "Your party has been created successfully !\n"

    def create_players_from_list(self, clients_list: list[int]) -> list[Player]:
        players_list = []
        assert self.repo, "The database should not be None"
        for client in clients_list:
            username = self.repo.get_username(str(client))
            players_list.append(Player(int(client), username, "None"))
        return players_list

    def check_profile_player(self, player_id: int) -> str:
        """Return a simple textual profile for the given player id."""
        assert self.repo is not None, "No games repository."
        profile = self.repo.get_player_profile(player_id)
        if profile is None:
            return "Player not found\n"
        return f"Player profile:\n username={profile['username']}\n status={profile['status']}\n score={profile['score']}\n "\
            f"wins={profile['stats_win']}\n loses={profile['stats_lose']}\n"

    def send_invitation(self, invited_player_id: str, invitee_player_id: str):
        username: str = self.repo.get_username(invited_player_id)
        invited_client: socket.socket = self.client_sockets[username]
        host_name: str = self.repo.get_username(invitee_player_id)
        message = f"Server: You have received an invitation from {host_name}.\n"
        message += f"Expires in 300s.\n"
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

    def get_game(self, client_id: str):
        assert self.repo is not None, "No games repository."
        party_id = int(self.repo.get_game(client_id))
        return self.current_games_list[party_id][1]
