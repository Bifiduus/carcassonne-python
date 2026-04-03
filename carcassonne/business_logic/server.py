import time
import socket
import select

from threading import Thread, Event, Lock
from carcassonne.business_logic.game.game import Game
from carcassonne.business_logic.interfaces.i_graph_data import IGraphData
from carcassonne.business_logic.online_communication import OnlineCommunication
from carcassonne.business_logic.player import Player
from carcassonne.datas.graph_data import GraphData
from carcassonne.datas.games_repository import GameRepository
from carcassonne.business_logic.interfaces.i_games_repository import (
    IGamesRepository,
)
from carcassonne.i18n import gettext as _
from carcassonne.presentation.interfaces.i_server_service import IServerService


class Server(IServerService):
    SERVER_TIMEOUT = 30
    SERVER_DIFFUSION_PERIOD = 10
    INVITATION_TIMEOUT = 300
    CLIENT_TIMEOUT = 60

    def __init__(self, repo: IGamesRepository | None = None, daemon: bool = False):
        # networking/server state
        self.server_name = socket.gethostbyname(socket.gethostname())
        self.server = None
        self.should_stop = Event()
        self.server_thread = None
        self.daemon = daemon
        # List to track connected client sockets
        self.connected_clients: list[socket.socket] = []
        self.clients_lock = Lock()  # Lock for thread-safe access
        # Needed to keep track of the different games
        self.current_games_list: dict[int, tuple[str, Game]] = {}
        # Map client_username -> socket
        self.client_sockets: dict[str, socket.socket] = {}
        # Map socket -> client_username
        self.player_clients: dict[socket.socket, str] = {}
        self.registered_clients: dict[socket.socket, bool] = {}
        # Track each client handler thread (for clean shutdown)
        self.client_threads: list[Thread] = []
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
            self.server.bind(("", int(port)))
            self.server.listen()
            self.server.settimeout(1.0)
            print(_("Server started on port {port}").format(port=port))
        except Exception as e:
            print(_("Error starting server: {error}").format(error=e))
            return
        self.should_stop.set()
        self.server_thread = Thread(
            target=self.server_running, args=(port,)
        )
        self.server_thread.start()

    def server_running(self, port):
        assert self.server
        first_diffusion = True
        server_last_diffusion = time.time()
        while self.server and self.should_stop.is_set():
            try:
                # Timeout to check self.running periodically
                self.server.settimeout(1.0)
                r, w, x = select.select([self.server], [], [], 1.0)
                for s in r:
                    if s is self.server:
                        client_socket, addr = self.server.accept()
                        # Add client to the list
                        with self.clients_lock:
                            self.connected_clients.append(client_socket)
                            self.registered_clients[client_socket] = False
                        # Handle client in a new thread
                        client_thread = Thread(
                            target=self.handle_client, args=(client_socket,)
                        )
                        client_thread.start()
                        self.client_threads.append(client_thread)
                        print(_("Accepted connection from a client."))

                # Timeout to check pending invitations periodically
                assert self.repo, "The database should not be None"
                timed_out = self.repo.check_all_invitations_timeout(
                    self.INVITATION_TIMEOUT
                )
                for player_id in timed_out:
                    user = self.repo.get_username(str(player_id))
                    self.send_to_client(user, "Your invitation timed out..")
                # Determine if a party can be launched, and if so, do it
                self.launch_availables_games()
                # Determine if a party ended, and if so, clean it
                self.clean_finished_games()
                self.check_client_timeouts()
                time_passed = time.time() - server_last_diffusion
                clock = self.SERVER_DIFFUSION_PERIOD
                if time_passed >= clock or first_diffusion:
                    server_last_diffusion = time.time()
                    host_name = socket.gethostname()
                    message = f"{socket.gethostbyname(host_name)}:{port}"
                    socket_message = socket.socket(
                        socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP
                    )
                    socket_message.setsockopt(
                        socket.SOL_SOCKET, socket.SO_BROADCAST, 1
                    )
                    broadcast_addr = ("<broadcast>", 12346)
                    socket_message.sendto(message.encode(), broadcast_addr)
                    socket_message.close()
                    if first_diffusion:
                        first_diffusion = False

            except socket.timeout:
                continue  # Check self.running again
            except Exception as e:
                if self.should_stop.is_set():
                    print(
                        _("Error accepting connection: {error}").format(
                            error=e
                        )
                    )
                break
        print(_("Server stopped."))

    def check_client_timeouts(self):
        """Check for clients that have exceeded their timeout
          and handle them."""
        assert self.repo is not None, "No games repository."
        self.repo.check_all_remaining_timeouts(
            self.CLIENT_TIMEOUT)

    def launch_availables_games(self):
        # For all parties, check if game can be launched
        # If so launch it, and handle_party() ( like handle_client but
        #  for a game )
        for party in self.repo.get_parties():
            check = self.party_can_be_launched(party)
            # Check if players are ok for party to be launched
            if check:
                host_id: int = self.repo.get_host_from_party(party)
                players = self.repo.get_party(str(host_id))
                if len(players) <= 1:
                    client_username: str = self.repo.get_username(str(host_id))
                    self.send_to_client(
                        client_username, "You cannot play alone..."
                    )
                    self.repo.delete_party(party)
                    self.repo.change_status(str(host_id), "idle")
                    continue
                self.create_new_party(players, str(host_id))

    def party_can_be_launched(self, party_number: int) -> bool:
        host_id: int = self.repo.get_host_from_party(party_number)
        check = self.repo.check_all_invitations_resolved(str(host_id))
        if self.repo.party_is_launched(host_id):
            check = False
        return check

    def clean_finished_games(self):
        with self.clients_lock:
            games = self.current_games_list.copy()
            for game in games:
                check = self.game_is_finished(game)
                party = self.repo.get_group_from_game(game)
                check_2 = not self.repo.check_party_is_alive(party)
                if (check or check_2):
                    self.repo.clean_party(game)
                    del self.current_games_list[game]

    def game_is_finished(self, party: int) -> bool:
        check = self.current_games_list[party][1].end_game()
        return check

    def is_server_running(self) -> bool:
        return self.should_stop.is_set()

    def client_is_registered(self, client_socket: socket.socket) -> bool:
        try:
            return self.registered_clients.get(client_socket, False)
        except Exception:
            return False

    def handle_client(self, client_socket: socket.socket):
        """
        Handle communication with a single client.
        """

        try:
            while True:
                try:
                    data = client_socket.recv(1500)
                except (OSError, socket.error) as e:
                    # Socket closed or broken (during shutdown)
                    if not self.should_stop.is_set():
                        print(f"Socket error during recv: {e}")
                    break

                if not data or data.decode() == "":
                    continue

                try:
                    client, message = data.decode().split(":")
                except ValueError:
                    # Malformed message
                    continue

                message = message.strip()
                try:
                    client_index = self.repo.get_id_from_username(client)
                except Exception:
                    # Client not found
                    continue

                # Whether the client is registered or not,
                # if it sends "quit", we consider it as a disconnection
                if message == "quit":
                    answer = self.handle_communication.command_quit(client)
                    self.send_to_clients(answer)
                    break

                if self.client_is_registered(client_socket):
                    # Process data
                    response = self.process_message(str(client_index), message)
                    # fonction qui check le statut d'une invitation et
                    # l'envoie à l'host
                    if self.daemon:
                        answer = ""
                    else:
                        answer = (
                            f"Server -> Client{client_index}: "
                            f"{response}\n"
                        )

                    try:
                        client_socket.send(answer.encode())
                    except (OSError, socket.error, BrokenPipeError) as e:
                        # Socket broken during send
                        if not self.should_stop.is_set():
                            print(f"Socket error during send: {e}")
                        break
                else:
                    self.handle_client_registering(
                        message, client_socket, client_index
                    )
        except Exception as e:
            print(_("Error handling client: {error}").format(error=e))
            # Mark client as improper if they have a username (registered)
            if client_socket in self.player_clients:
                username: str = self.player_clients[client_socket]
                try:
                    self.repo.set_unproper_client(username)
                except Exception:
                    pass
        finally:
            # Handle improper client disconnections using repository
            if client_socket in self.player_clients:
                username: str = self.player_clients[client_socket]
                try:
                    if not self.repo.is_proper_client(username):
                        self.repo.set_timeout_for_player(
                            username, self.CLIENT_TIMEOUT)
                        self.handle_communication.command_quit(username)
                except Exception:
                    pass

            # Close socket safely
            try:
                client_socket.close()
            except (OSError, socket.error):
                # Already closed, that's fine
                pass

            # Remove client from the list
            with self.clients_lock:
                if client_socket in self.connected_clients:
                    self.connected_clients.remove(client_socket)
                if client_socket in self.player_clients:
                    username = self.player_clients[client_socket]
                    try:
                        del self.client_sockets[username]
                    except KeyError:
                        pass
                    try:
                        del self.player_clients[client_socket]
                    except KeyError:
                        pass
                    try:
                        del self.registered_clients[client_socket]
                    except KeyError:
                        pass

    def handle_client_registering(
        self, message: str, client_socket: socket.socket, client_index: int
    ):
        """
        Process client registering and return a response.
        """
        preface = f"Server -> Client{client_index}: "
        if (message.find("username=") != -1 and
                message.find("password=") != -1):
            username, password = message.split(" password=")
            username: str = username.removeprefix(
                "username=")
            success = self.repo.registering(username, password)
            if not self.repo.is_proper_client(username):
                remaining_timeout = self.repo.get_remaining_timeout(
                    username)
                if remaining_timeout > 0:
                    answer = f"{preface}You are under a timeout of"
                    f" {remaining_timeout}s !\n"
                    success = False
            if success:
                answer = f"{preface}Successfull registering !\n"
                with self.clients_lock:
                    self.registered_clients[client_socket] = True
                    self.client_sockets[username] = client_socket
                    self.player_clients[client_socket] = username
                self.send_to_clients(f"{username} is now connected !\n")
            else:
                answer = f"{preface}Your registration has failed...\n"
        else:
            answer = f"{preface}You should send your username"\
                " and password !\n"
        client_socket.send(answer.encode())

    def send_to_clients(self, message: str):
        preface: str = "Server -> Client"
        with self.clients_lock:
            for client_socket in list(self.client_sockets.values()):
                try:
                    if client_socket not in self.player_clients:
                        continue
                    username: str = self.player_clients[client_socket]
                    id = self.repo.get_id_from_username(username)
                    formatted_message = preface + f"{id}: " + message
                    client_socket.send(formatted_message.encode())
                except Exception as e:
                    print(f"Error sending to client: {e}")

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
            elif message == "Bad client disconnection":
                answer = self.handle_communication.command_quit(
                    client_id)
                self.repo.set_unproper_client(
                    self.repo.get_username(client_id))
            elif message == "server status":
                answer = self.handle_communication.command_server_status()
            elif message.startswith("new"):
                answer = self.handle_communication.command_new(
                    message, client_id
                )
            elif message.startswith("players"):
                answer = self.handle_communication.command_players(message)
            elif message.startswith("play"):
                answer = self.handle_communication.command_play(
                    message, client_id
                )
            elif message == "scoreboard":
                answer = self.handle_communication.command_scoreboard()
            elif message == "accept":
                answer = self.handle_communication.command_accept(client_id)
            elif message == "decline":
                answer = self.handle_communication.command_decline(client_id)
            elif message.startswith("cancel"):
                answer = self.handle_communication.command_cancel(
                    client_id, message.strip("cancel")
                )
            elif message == "away":
                answer = self.handle_communication.command_away(client_id)
            elif message == "back":
                answer = self.handle_communication.command_back(client_id)
            elif message == "board":
                answer = self.handle_communication.command_board(client_id)
            elif message.startswith("set"):
                answer = self.handle_communication.command_set(
                    client_id, message
                )
            elif message == "show configuration":
                answer = self.handle_communication.command_config(client_id)
            elif message == "show history":
                answer = self.handle_communication.command_history(client_id)
            elif message == "show score":
                answer = self.handle_communication.command_score(client_id)
            elif message == "show hand":
                answer = self.handle_communication.command_hand(client_id)
            elif message == "redo":
                answer = self.handle_communication.command_redo(client_id)
            elif message == "undo":
                answer = self.handle_communication.command_undo(client_id)
            elif message == "hint":
                answer = self.handle_communication.command_hint(client_id)
            elif message == "draw":
                answer = self.handle_communication.command_draw(client_id)
            elif message == "shuffle":
                answer = self.handle_communication.command_shuffle(client_id)
            elif message.startswith("save "):
                answer = self.handle_communication.command_save(
                    client_id, message
                )
            elif message.startswith("load "):
                answer = self.handle_communication.command_load(
                    client_id, message
                )
        return answer

    def check_clients_list_validity(
        self, clients_list: list[str]
    ) -> list[str]:
        """Verify that each client id refers to
        an existing player via the repository."""
        assert self.repo is not None, "No games repository."
        return [
            c
            for c in clients_list
            if self.repo.player_exists(self.repo.get_username(c))
        ]

    def create_new_party(
        self, clients_list: list[int], client_id: str, party_name: str = ""
    ) -> str:
        assert self.repo is not None, "No games repository."
        party_id = self.repo.get_party_id(client_id)
        if party_name == "":
            party_name = f"Party {party_id}"
        # Initialize the game
        number_of_players_in_group: int = len(clients_list)
        graph: IGraphData = GraphData()
        new_party = Game(graph, number_of_players_in_group)
        try:
            self.repo.create_game(party_name, party_id)
            game_id: int = self.repo.get_game_id(party_id)
            self.current_games_list[game_id] = (party_name, new_party)
            players_list = self.create_players_from_list(clients_list)
            new_party.start_online_game(players_list)
            for player_id in clients_list:
                self.repo.change_status(str(player_id), "ingame")
        except Exception as e:
            print(f"Error creating party in repository: {e}")
        return "Your party has been created successfully !\n"

    def create_players_from_list(
        self, clients_list: list[int]
    ) -> list[Player]:
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
        return (
            f"Player profile:\n username={profile['username']}\n "
            f"status={profile['status']}\n score={profile['score']}\n "
            f"wins={profile['stats_win']}\n loses={profile['stats_lose']}\n"
        )

    def send_invitation(self, invited_player_id: str, invitee_player_id: str):
        username: str = self.repo.get_username(invited_player_id)
        invited_client: socket.socket = self.client_sockets[username]
        host_name: str = self.repo.get_username(invitee_player_id)
        message = "Server: You have received an invitation "\
            f"from {host_name}.\n"
        message += f"Expires in {self.INVITATION_TIMEOUT}s.\n"
        with self.clients_lock:
            try:
                assert self.repo, "The database should not be None"
                ok = self.repo.send_invitation(
                    invited_player_id,
                    invitee_player_id,
                )
                if ok:
                    invited_client.sendall(message.encode())
        except KeyError:
            print(f"Client socket not found for {invited_player_id}")
        except Exception as e:
            print(f"Error sending invitation: {e}")

    def server_stop(self):
        """
        Stop the server gracefully with proper resource cleanup.
        """
        print("Starting server shutdown...")

        if self.server_thread is not None:
            # 1. Signal server loop to stop
            self.should_stop.clear()

            # 2. Close the server socket immediately
            #  to stop accepting connections
            if self.server:
                try:
                    self.server.close()
                except Exception as e:
                    print(f"Error closing server socket: {e}")
                self.server = None

            # 3. Notify and close all connected clients
            shutdown_message = "Server Shutdown\n"
            with self.clients_lock:
                for client_socket in self.connected_clients[:]:
                    try:
                        client_socket.sendall(shutdown_message.encode())
                        # Ensure the client is marked as proper to
                        #  avoid handling them as abrupt disconnects
                        username = self.player_clients.get(
                            client_socket, "Unknown")
                        self.repo.client_quit(username)
                    except Exception as e:
                        print(f"Error sending shutdown message: {e}")
                    finally:
                        try:
                            client_socket.close()
                        except Exception as e:
                            print(f"Error closing client socket: {e}")
                self.connected_clients.clear()

            # 4. Clean up active games
            with self.clients_lock:
                current_games = list(self.current_games_list.items())
                for game_id, (party_name, game) in current_games:
                    try:
                        # Save game state or perform cleanup
                        print(f"Cleaning up game: {party_name}")
                        game = self.current_games_list.pop(game_id, None)
                        if game:
                            # Perform any necessary cleanup
                            #  on the game instance
                            game[1].save_game_to_file(
                                f"game_{party_name}_"
                                f"{time.asctime(time.localtime())}_backup.txt")
                    except Exception as e:
                        print(f"Error cleaning up game {game_id}: {e}")
                self.current_games_list.clear()

            # 5. Clear client tracking dictionaries
            with self.clients_lock:
                self.client_sockets.clear()
                self.player_clients.clear()
                self.registered_clients.clear()

            # 6. Wait for client threads to finish (with timeout)
            for t in self.client_threads:
                if t.is_alive():
                    try:
                        t.join(timeout=2.0)
                    except Exception as e:
                        print(f"Error joining client thread: {e}")
                    if t.is_alive():
                        print("Warning: a client thread did"
                              " not finish in time")

            # 7. Close repository
            if hasattr(self, 'repo') and self.repo:
                try:
                    self.repo.close()
                except Exception as e:
                    print(f"Error closing repository: {e}")

            # 8. Wait for server thread to finish (with timeout)
            try:
                self.server_thread.join(timeout=5.0)
                if self.server_thread.is_alive():
                    print("Warning: Server thread did not"
                          " terminate within timeout")
            except Exception as e:
                print(f"Error joining server thread: {e}")

            print("Server shutdown complete")

    def get_game(self, client_id: str):
        assert self.repo is not None, "No games repository."
        group_id = self.repo.get_party_id(client_id)
        game_id = self.repo.get_game_id(group_id)
        return self.current_games_list[game_id][1]

    def send_to_group(self, group_id: int, message: str) -> bool:
        players: list[str] = self.repo.get_players_from_group(group_id)
        ok = True
        for player in players:
            ok = self.send_to_client(player, message)
        return ok

    def send_to_client(self, username: str, message: str) -> bool:
        with self.clients_lock:
            try:
                if username not in self.client_sockets:
                    print(f"Client {username} socket not found")
                    return False
                client_socket = self.client_sockets[username]
                client_index = self.repo.get_id_from_username(username)
                preface = f"Server -> Client{client_index}"
                client_socket.send(f"{preface}: {message}\n".encode())
                return True
            except KeyError:
                print(f"Client {username} socket not found")
                return False
            except Exception as e:
                print(f"Error sending to client {username}: {e}")
                return False
