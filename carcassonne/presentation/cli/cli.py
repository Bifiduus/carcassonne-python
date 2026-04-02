"""Command-line interface for the Carcassonne game.

GameCLI accepts commands to start/load/save games, draw and place tiles,
undo/redo turns, and display game state information.
"""

from carcassonne.presentation.interfaces.i_client_service import IClientService
from carcassonne.presentation.interfaces.i_game_service import IGameService
from carcassonne.presentation.cli import commands_handler_cli

import readline
import threading
import time

from carcassonne.presentation.interfaces.i_server_service import IServerService

COMMANDS = [
    "new",
    "help",
    "quit",
    "load",
    "save",
    "shuffle",
    "draw",
    "hint",
    "undo",
    "redo",
    "show hand",
    "show time",
    "show score",
    "show history",
    "show configuration",
    "set",
    "server start",
    "server stop",
    "join",
    "players",
    "server list",
    "ping",
    "scoreboard",
    "accept",
    "decline",
    "cancel",
    "away",
    "back",
]


def completer(texte, state):

    # filtrer les commandes qui commencent par text
    line = readline.get_line_buffer()
    prefix = line[:-len(texte)] if texte else line
    matches = [cmd for cmd in COMMANDS if cmd.startswith(prefix + texte)]
    if state < len(matches):
        return matches[state][len(prefix):]
    else:
        return None


class GameCLI:

    def __init__(
        self,
        game_service: IGameService,
        server_service: IServerService,
        client_service: IClientService,
    ):
        self.server = server_service
        self.client = client_service
        self.game = game_service
        self.settings = self.game.get_game_configuration()
        self.local_player_id = self.game.get_current_player().get_id()
        self.running = True
        self._tick_interval_seconds = 0.1
        self._tick_sleep_seconds = 0.01
        self._tick_last_message = ""
        self._stop_event = threading.Event()
        self._game_lock = threading.RLock()
        self._input_thread: threading.Thread | None = None

        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")

        try:
            readline.read_history_file('.carcassonne_history')
        except FileNotFoundError:
            pass

    def _is_turn_bound_command(self, command: str) -> bool:
        return (
            command == "draw"
            or command == "hint"
            or command == "undo"
            or command == "redo"
            or command.startswith("play")
        )

    def _local_player_can_act(self) -> bool:
        return self.game.get_current_player().get_id() == self.local_player_id

    def run(self):
        print("Welcome to Carcassonne")
        print("Type 'help' for the list of commands.\n")

        self._start_input_loop()
        last_tick = time.monotonic()

        try:
            while self.running:
                now = time.monotonic()
                if now - last_tick >= self._tick_interval_seconds:
                    with self._game_lock:
                        self._tick_once()
                    last_tick = now
                time.sleep(self._tick_sleep_seconds)
        except KeyboardInterrupt:
            print("\nFin de partie.")
            self.running = False
        finally:
            self._stop_event.set()
            if self._input_thread is not None:
                self._input_thread.join(timeout=0.2)
            readline.write_history_file('.carcassonne_history')

    def _start_input_loop(self) -> None:
        if self._input_thread is not None and self._input_thread.is_alive():
            return
        self._input_thread = threading.Thread(
            target=self._input_loop,
            name="carcassonne-cli-input",
            daemon=True,
        )
        self._input_thread.start()

    def _input_loop(self) -> None:
        while self.game.get_current_player().is_ai_player():
            self.game.play_ai_turn()

        while (
            self.game.get_current_player().is_ai_player()
            and not self.game.end_game()
        ):
            with self._game_lock:
                if not self.running or self.game.end_game():
                    break
                self.game.play_ai_turn()

        if self.game.end_game():
            self._on_game_over()
            return

        while self.running and not self._stop_event.is_set():
            try:
                command = input(">> ").strip()
            except EOFError:
                self.running = False
                break
            except KeyboardInterrupt:
                print("\nFin de partie.")
                self.running = False
                break

            with self._game_lock:
                if not self.running:
                    break
                self.handle_command(command)

    def _tick_once(self) -> None:
        self.game.tick_blitz()
        timeout_message = str(self.game.get_timeout_message() or "")
        clean_message = timeout_message.strip()
        if clean_message and clean_message != self._tick_last_message:
            print(f"\n{clean_message}")
            self._tick_last_message = clean_message

        if self.game.end_game():
            self._on_game_over()
            return

        if (
            not self._local_player_can_act()
            and not self.game.end_game()
            and self.game.get_current_player().is_ai_player()
        ):
            self.game.play_ai_turn()
            self.game.get_board()

    def _on_game_over(self) -> None:
        """Display final scores and stop the game loop."""
        if not self.running:
            return
        self.running = False
        self._stop_event.set()
        self.game.get_board()
        print("\n=== Partie terminée ! Scores finaux ===")
        players_order = self.game.get_players_order()
        results = []
        for pid in players_order:
            player = self.game.game_data.players[pid]
            username = player.get_username()
            score = player.get_score_int()
            results.append((score, username))
        results.sort(key=lambda x: -x[0])
        for rank, (score, username) in enumerate(results, start=1):
            print(f"  {rank}. {username}: {score} points")

    def handle_command(self, command):
        is_turn_bound_command = self._is_turn_bound_command(command)
        if is_turn_bound_command and not self._local_player_can_act():
            print(
                "Commande refusée: ce n'est pas votre tour"
                " ou votre temps est écoulé."
            )
            return

        if command.startswith("new"):
            args = command[4:].strip()
            commands_handler_cli.new_game(self, args, self.client)
            self.local_player_id = self.game.get_current_player().get_id()
            self._tick_last_message = ""
        elif command == "help":
            commands_handler_cli.help(self)
        elif command == "quit":
            commands_handler_cli.quit(self, self.server, self.client)
        elif command.startswith("load "):
            filename = command[5:].strip()
            commands_handler_cli.load(self, filename, self.client)
            self.local_player_id = self.game.get_current_player().get_id()
            self._tick_last_message = ""
        elif command.startswith("save "):
            filename = command[5:].strip()
            commands_handler_cli.save(self, filename, self.client)
        elif command == "shuffle":
            commands_handler_cli.shuffle(self, self.client)
        elif command == "draw":
            commands_handler_cli.draw(self, self.client)
        elif command == "hint":
            commands_handler_cli.hint(self, self.client)
        elif command == "undo":
            commands_handler_cli.undo(self, 1, self.client)
        elif command == "redo":
            commands_handler_cli.redo(self, 1, self.client)
        elif command == "show hand":
            commands_handler_cli.show_hand(self, self.client)
        elif command == "show time" or command.startswith("show time "):
            player_id_arg = command[len("show time"):].strip()
            commands_handler_cli.show_time(self, player_id_arg or None)
        elif command == "show score":
            commands_handler_cli.show_score(self, self.client)
        elif command == "show history":
            commands_handler_cli.show_history(
                self, game=self.game, client_service=self.client
            )
        elif command == "show configuration":
            commands_handler_cli.show_configuration(
                self, game=self.game, client_service=self.client
            )
        elif command.startswith("set"):
            content = command[3:].strip()
            if "=" in content:
                param, value = content.split("=", 1)
                param = param.strip()
                value = value.strip()
            else:
                param = content
                value = None
            commands_handler_cli.set_parameter(self, param, value, self.client)
        elif command.startswith("players"):
            commands_handler_cli.players(self, self.client, command)
        elif command.startswith("play "):
            move = command[5:].strip()
            commands_handler_cli.play(
                self, move, game=self.game, client_service=self.client
            )
        elif command.startswith("board"):
            commands_handler_cli.show_board(
                self, game=self.game, client_service=self.client
            )
        elif command == "server list":
            commands_handler_cli.show_server_list(self, self.client)
        elif command.startswith("server start"):
            port = command.strip("server start")
            commands_handler_cli.server_start(self, port, self.server)
        elif command == "server stop":
            commands_handler_cli.stop_server(self, self.server)
        elif command.startswith("join"):
            addresse = command[5:].strip()
            if ":" in addresse:
                ip, port = addresse.split(":")
                commands_handler_cli.join(self, self.client, ip, port)
            else:
                commands_handler_cli.join(self, self.client, addresse)
        elif command == "ping":
            commands_handler_cli.ping(self, self.client)
        elif command == "server status":
            commands_handler_cli.server_status(self, self.client)
        elif command == "scoreboard":
            commands_handler_cli.scoreboard(self, self.client)
        elif command == "accept":
            commands_handler_cli.accept(self, self.client)
        elif command == "decline":
            commands_handler_cli.decline(self, self.client)
        elif command == "cancel":
            commands_handler_cli.cancel(self, self.client)
        elif command == "back":
            commands_handler_cli.back(self, self.client)
        elif command == "away":
            commands_handler_cli.away(self, self.client)

        else:
            print(
                "Commande inconnue. Tapez 'help' pour la liste des commandes."
            )

        if command:
            readline.add_history(command)
