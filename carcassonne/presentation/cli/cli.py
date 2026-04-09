"""Command-line interface for the Carcassonne game.

GameCLI accepts commands to start/load/save games, draw and place tiles,
undo/redo turns, and display game state information.
"""

from carcassonne.interfaces.i_client_service import IClientService
from carcassonne.interfaces.i_game_service import IGameService
from carcassonne.presentation.cli import commands_handler_cli

import os
import readline
import signal
import threading
import time

from carcassonne.i18n import gettext as _
from carcassonne.interfaces.i_server_service import IServerService

# All command prefixes exposed by TAB completion.
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

# Stores the last ambiguous query handled by completer so we can emulate
# "first TAB beeps, second TAB lists candidates" behavior.
_LAST_AMBIGUOUS_QUERY = ""


class GameFinishedInterrupt(Exception):
    """Internal control-flow exception used to stop a blocking prompt."""


def completer(texte, state):
    """Readline completer with two-step behavior on ambiguous matches.

    First TAB on an ambiguous prefix emits a bell, second TAB prints
    candidates.
    """
    global _LAST_AMBIGUOUS_QUERY

    # filtrer les commandes qui commencent par text
    line = readline.get_line_buffer()
    prefix = line[:-len(texte)] if texte else line
    query = prefix + texte
    matches = [cmd for cmd in COMMANDS if cmd.startswith(query)]

    if len(matches) == 0:
        if state == 0:
            print("\a", end="", flush=True)
        _LAST_AMBIGUOUS_QUERY = ""
        return None

    if len(matches) == 1:
        _LAST_AMBIGUOUS_QUERY = ""
        if state == 0:
            return matches[0][len(prefix):]
        return None

    # Ambiguous completion: first TAB beeps, second TAB lists candidates.
    if state == 0:
        if _LAST_AMBIGUOUS_QUERY != query:
            _LAST_AMBIGUOUS_QUERY = query
            print("\a", end="", flush=True)
            # Keep the current input unchanged.
            return ""

        print()
        for candidate in matches:
            print(candidate)
        # Keep query so following TAB presses continue listing choices
        # without beeping again, until input changes.
        return ""

    return None


class GameCLI:
    """Interactive CLI runner coordinating input loop and game ticks."""

    def __init__(
        self,
        game_service: IGameService,
        server_service: IServerService,
        client_service: IClientService,
    ):
        """Initialize CLI state and configure readline history/completion."""
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
        self._tick_thread: threading.Thread | None = None
        self._wakeup_signal = getattr(signal, "SIGUSR1", None)
        self._previous_wakeup_handler = None

        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete")

        try:
            readline.read_history_file('.carcassonne_history')
        except FileNotFoundError:
            pass

    def _is_turn_bound_command(self, command: str) -> bool:
        """Return True when command requires the local player to be active."""
        return (
            command == "draw"
            or command == "hint"
            or command == "undo"
            or command.startswith("undo ")
            or command == "redo"
            or command.startswith("redo ")
            or command.startswith("play")
        )

    def _local_player_can_act(self) -> bool:
        """Return whether the local player currently owns the active turn."""
        return self.game.get_current_player().get_id() == self.local_player_id

    def _handle_game_finished_signal(self, signum, frame) -> None:
        """Interrupt blocking input when the game ends from another thread."""
        raise GameFinishedInterrupt()

    def _install_wakeup_signal_handler(self) -> None:
        """Install temporary signal handler used to wake the input prompt."""
        if self._wakeup_signal is None:
            return
        self._previous_wakeup_handler = signal.getsignal(self._wakeup_signal)
        signal.signal(self._wakeup_signal, self._handle_game_finished_signal)

    def _restore_wakeup_signal_handler(self) -> None:
        """Restore the signal handler that was active before CLI startup."""
        if self._wakeup_signal is None:
            return
        previous_handler = self._previous_wakeup_handler
        if previous_handler is None:
            previous_handler = signal.SIG_DFL
        signal.signal(self._wakeup_signal, previous_handler)
        self._previous_wakeup_handler = None

    def _wake_input_prompt(self) -> None:
        """Send wake-up signal to unblock input() in the main thread."""
        if self._wakeup_signal is None:
            return
        if threading.current_thread() is threading.main_thread():
            return
        try:
            os.kill(os.getpid(), self._wakeup_signal)
        except OSError:
            return

    def _start_tick_loop(self) -> None:
        """Start background tick loop once (idempotent)."""
        if self._tick_thread is not None and self._tick_thread.is_alive():
            return
        self._tick_thread = threading.Thread(
            target=self._tick_loop,
            name="carcassonne-cli-tick",
        )
        self._tick_thread.start()

    def _tick_loop(self) -> None:
        """Background periodic loop that drives blitz and AI turns."""
        last_tick = time.monotonic()
        while self.running and not self._stop_event.is_set():
            now = time.monotonic()
            if now - last_tick >= self._tick_interval_seconds:
                with self._game_lock:
                    if not self.running or self._stop_event.is_set():
                        break
                    self._tick_once()
                last_tick = now
            time.sleep(self._tick_sleep_seconds)

    def run(self):
        """Run the interactive CLI session until quit or game over."""
        with self._game_lock:
            if not self.game.end_game():
                self._render_board()
                self._tick_once()

        if not self.running or self._stop_event.is_set():
            readline.write_history_file('.carcassonne_history')
            return

        self._install_wakeup_signal_handler()
        self._start_tick_loop()
        try:
            while self.running and not self._stop_event.is_set():
                try:
                    command = input(">> ").strip()
                except GameFinishedInterrupt:
                    if not self.running or self._stop_event.is_set():
                        break
                    continue
                except EOFError:
                    self.running = False
                    break
                except KeyboardInterrupt:
                    print("\n" + _("Game over."))
                    self.running = False
                    break

                with self._game_lock:
                    if not self.running or self._stop_event.is_set():
                        break
                    self.handle_command(command)
        except KeyboardInterrupt:
            print("\n" + _("Game over."))
            self.running = False
        finally:
            self._stop_event.set()
            if self._tick_thread is not None:
                self._tick_thread.join(timeout=0.2)
            self._restore_wakeup_signal_handler()
            readline.write_history_file('.carcassonne_history')

    def _render_board(self) -> None:
        """Print the board while preserving trailing newline rules."""
        board = self.game.get_printed_board()
        if not board.endswith("\n"):
            board += "\n"
        print(board, end="")

    def _tick_once(self) -> None:
        """Execute one periodic tick: blitz, timeout messages, AI turn."""
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
            self.game.play_ai_turn(self.game)
            commands_handler_cli._print_scores(self.game)
            self._render_board()

    def _on_game_over(self) -> None:
        """Display final scores and stop the game loop."""
        if not self.running:
            return
        print()
        self.running = False
        self._stop_event.set()
        self._render_board()
        print("\n" + _("=== Game finished! Final scores ==="))
        winner = self.game.get_winner()
        if winner is None:
            winners = self.game.get_winners()
            if winners:
                names = ", ".join(
                    player.get_username() for player in winners
                )
                print(_("Draw: {players}").format(players=names))
        else:
            print(
                _("Winner: {player}").format(
                    player=winner.get_username(),
                )
            )
        players_order = self.game.get_players_order()
        results = []
        for pid in players_order:
            player = self.game.game_data.players[pid]
            username = player.get_username()
            score = player.get_score_int()
            results.append((score, username))
        results.sort(key=lambda x: -x[0])
        for rank, (score, username) in enumerate(results, start=1):
            print(
                _("  {rank}. {username}: {score} points").format(
                    rank=rank,
                    username=username,
                    score=score,
                )
            )
        self._wake_input_prompt()

    def handle_command(self, command):
        """Parse one raw command line and dispatch to command handlers."""
        is_turn_bound_command = self._is_turn_bound_command(command)
        if is_turn_bound_command and not self._local_player_can_act():
            print(
                _(
                    "Command rejected: it is not your turn"
                    " or your time has run out."
                )
            )
            return

        if command == "new" or command.startswith("new "):
            args = command[4:].strip()
            if commands_handler_cli.new_game(self, args, self.client):
                self.local_player_id = self.game.get_current_player().get_id()
                self._tick_last_message = ""
        elif command == "help" or command.startswith("help "):
            help_command = command[4:].strip() or None
            commands_handler_cli.help(self, help_command)
        elif command == "quit":
            commands_handler_cli.quit(self, self.server, self.client)
        elif command == "load":
            print(_("Usage: load FILE"))
        elif command.startswith("load "):
            filename = command[5:].strip()
            if not filename:
                print(_("Usage: load FILE"))
            else:
                commands_handler_cli.load(self, filename, self.client)
                self.local_player_id = self.game.get_current_player().get_id()
                self._tick_last_message = ""
        elif command == "save":
            print(_("Usage: save FILE"))
        elif command.startswith("save "):
            filename = command[5:].strip()
            if not filename:
                print(_("Usage: save FILE"))
            else:
                commands_handler_cli.save(self, filename, self.client)
        elif command == "shuffle":
            commands_handler_cli.shuffle(self, self.client)
        elif command == "draw":
            commands_handler_cli.draw(self, self.client)
        elif command == "hint":
            commands_handler_cli.hint(self, self.client)
        elif command == "undo" or command.startswith("undo "):
            count_arg = command[4:].strip()
            if not count_arg:
                commands_handler_cli.undo(self, 1, self.client)
            else:
                try:
                    count = int(count_arg)
                    if count < 1:
                        raise ValueError
                except ValueError:
                    print(_("Usage: undo [N]"))
                else:
                    commands_handler_cli.undo(self, count, self.client)
        elif command == "redo" or command.startswith("redo "):
            count_arg = command[4:].strip()
            if not count_arg:
                commands_handler_cli.redo(self, 1, self.client)
            else:
                try:
                    count = int(count_arg)
                    if count < 1:
                        raise ValueError
                except ValueError:
                    print(_("Usage: redo [N]"))
                else:
                    commands_handler_cli.redo(self, count, self.client)
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
        elif command == "set":
            print(_("Usage: set PARAM=VALUE"))
        elif command.startswith("set "):
            content = command[3:].strip()
            if "=" in content:
                param, value = content.split("=", 1)
                param = param.strip()
                value = value.strip()
                if not param:
                    print(_("Usage: set PARAM=VALUE"))
                else:
                    commands_handler_cli.set_parameter(
                        self, param, value, self.client
                    )
            else:
                print(_("Usage: set PARAM=VALUE"))
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
        elif command == "server start" or command.startswith("server start "):
            port = command.removeprefix("server start").strip()
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
                _("Unknown command. Type 'help' to see the list of commands.")
            )

        if command:
            readline.add_history(command)
