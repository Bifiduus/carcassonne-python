"""Command handlers used by the Carcassonne CLI.

Each function in this module implements one user-facing command and delegates
the actual game operations to the active services or game object.
"""

import shlex

from carcassonne.interfaces.i_client_service import IClientService
from carcassonne.i18n import gettext as _
from carcassonne.interfaces.i_server_service import IServerService


def new_game(self, args, client_service: IClientService) -> bool:
    """Start a new game locally or forward the command to the server."""
    if client_service.connected_to_a_server():
        client_service.send_to_server("new " + args)
        return True
    try:
        options = _parse_new_game_args(args)
        self.game.start_new_game_from_options(**options)
    except ValueError as error:
        print(_("Invalid new command: {error}").format(error=error))
        return False
    print(_("New game started."))
    return True


def _parse_new_game_args(raw_args: str) -> dict[str, object]:
    """Parse CLI arguments for ``new`` into typed option dictionary."""
    if not raw_args.strip():
        return {}

    option_aliases = {
        "ai": "num_ai_players",
        "ia": "num_ai_players",
        "num_ai_players": "num_ai_players",
        "color": "player_color",
        "colour": "player_color",
        "couleur": "player_color",
        "seed": "seed",
    }
    int_options = {"num_ai_players", "seed"}
    parsed_options: dict[str, object] = {}

    try:
        tokens = shlex.split(raw_args)
    except ValueError as error:
        raise ValueError(
            _("unable to parse arguments: {error}").format(error=error)
        ) from error

    for token in tokens:
        if "=" not in token:
            raise ValueError(
                _(
                    "expected KEY=VALUE arguments such as "
                    "'ai=2 color=red seed=42', got '{token}'"
                ).format(token=token)
            )
        raw_key, raw_value = token.split("=", 1)
        key = option_aliases.get(raw_key.strip().lower())
        if key is None:
            raise ValueError(
                _("unknown new-game option: {option}").format(
                    option=raw_key.strip()
                )
            )
        if key in parsed_options:
            raise ValueError(
                _("duplicate new-game option: {option}").format(
                    option=raw_key.strip()
                )
            )
        value = raw_value.strip()
        if value == "":
            raise ValueError(
                _("missing value for new-game option: {option}").format(
                    option=raw_key.strip()
                )
            )
        if key in int_options:
            try:
                parsed_options[key] = int(value)
            except ValueError as error:
                raise ValueError(
                    _("invalid integer for {option}: {value}").format(
                        option=raw_key.strip(),
                        value=value,
                    )
                ) from error
        else:
            parsed_options[key] = value.lower()

    return parsed_options


def _display_value(value) -> str:
    """Format a configuration value for user-friendly CLI display."""
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


def _apply_history_action(game, action_name: str, count: int) -> int:
    """Apply undo/redo repeatedly and return how many actions changed state."""
    if action_name == "undo":
        action_many = getattr(game, "undo_moves", None)
        action_single = game.undo
        history_attr = "past_moves"
    else:
        action_many = getattr(game, "redo_moves", None)
        action_single = game.redo
        history_attr = "future_moves"

    if callable(action_many):
        return action_many(count)

    changed = 0
    for _step in range(count):
        available_moves = getattr(game.game_data.history, history_attr, [])
        if len(available_moves) == 0:
            break
        before_past = len(game.game_data.history.past_moves)
        before_future = len(game.game_data.history.future_moves)
        action_single()
        after_past = len(game.game_data.history.past_moves)
        after_future = len(game.game_data.history.future_moves)
        if before_past == after_past and before_future == after_future:
            break
        changed += 1
    return changed


def _command_help_lines() -> dict[str, str]:
    """Return command->help-line mapping used by ``help`` command."""
    return {
        "new": _(
            "  new [ARGS]         - Start a new game "
            "(ai=N color=COLOR seed=SEED)"
        ),
        "help": _(
            "  help [CMD]         - Display help for all commands or CMD"
        ),
        "quit": _("  quit               - Quit the game"),
        "load": _("  load <file>        - Load a game from a file"),
        "save": _("  save <file>        - Save the game to a file"),
        "shuffle": _("  shuffle            - Shuffle the deck"),
        "draw": _("  draw               - Draw a tile"),
        "hint": _("  hint               - Show a hint for the current tile"),
        "undo": _(
            "  undo [N]           - Undo the last move or the last N moves"
        ),
        "redo": _(
            "  redo [N]           - Redo the last undone move or the last "
            "N undone moves"
        ),
        "show hand": _(
            "  show hand          - Display the current player's hand"
        ),
        "show time": _(
            "  show time [ID]     - Display the remaining time of all "
            "players or of player ID"
        ),
        "show score": _(
            "  show score         - Display the players' scores"
        ),
        "show history": _(
            "  show history       - Display the move history"
        ),
        "show configuration": _(
            "  show configuration - Display the current game configuration"
        ),
        "set": _("  set PARAM=VALUE    - Set a configuration parameter"),
        "play": _("  play <move>        - Play the specified move"),
        "server start": _(
            "  server start [PORT] - Start the server on port [PORT]"
        ),
        "server list": _(
            "  server list        - Display the list of available servers"
        ),
        "server stop": _("  server stop        - Stop the server"),
        "join": _(
            "  join [IP[:PORT]]   - Connect the client to the given server "
            "or to its own server"
        ),
        "ping": _("  ping               - Display the server ping"),
        "server status": _(
            "  server status      - Display the server status"
        ),
        "players": _(
            "  players [PLAYER_ID] - Display connected players or "
            "information about player [PLAYER_ID]"
        ),
        "scoreboard": _(
            "  scoreboard         - Display the server scoreboard"
        ),
        "accept": _("  accept             - Accept the received invitation"),
        "decline": _("  decline            - Decline the received invitation"),
        "cancel": _("  cancel             - Cancel the sent invitation"),
        "away": _('  away               - Change the status to "away"'),
        "back": _('  back               - Change the status to "idle"'),
    }


def help(self, command_name: str | None = None) -> None:
    """Print global help or detailed help for a single command."""
    command_help = _command_help_lines()
    if command_name is None:
        print(_("Available commands:"))
        for line in command_help.values():
            print(line)
        return

    normalized_command = " ".join(command_name.split())
    help_line = command_help.get(normalized_command)
    if help_line is None:
        print(
            _("Unknown command. Type 'help' to see the list of commands.")
        )
        return
    print(help_line)


def quit(
    self, server_service: IServerService, client_service: IClientService
) -> None:
    """Quit session safely, optionally prompting to save unsaved progress."""
    if client_service.connected_to_a_server():
        client_service.send_to_server("quit")
        return
    if server_service.is_server_running():
        print(_("You should close your server first."))
        return
    if self.game.has_unsaved_changes():
        while True:
            confirm = input(_("Save the game before quitting? [y/N] ")).strip()
            if confirm not in ("y", "Y"):
                break
            filename = input(_("Save file name: "))
            if save(self, filename, client_service) == 0:
                break
    print(_("Quitting the game. See you soon!"))
    self.running = False


def load(self, filename, client_service: IClientService) -> None:
    """Load a game from file locally or delegate to remote server."""
    if client_service.connected_to_a_server():
        client_service.send_to_server(f"load {filename}")
    else:
        if self.game.load_game_from_file(filename) == 0:
            # Re-initialize river_manager with the loaded config
            self.game.river_manager.reset()
            if self.game.game_data.game_configuration.get_setting_value(
                "river"
            ):
                self.game.river_manager.initialize_river()
            print(
                _("Game loaded from {filename}.").format(filename=filename)
            )
        else:
            print(
                _("Failed to load the game from {filename}.").format(
                    filename=filename
                )
            )


def save(self, filename, client_service: IClientService) -> int | None:
    """Save local game to file or forward save request to server."""
    if client_service.connected_to_a_server():
        client_service.send_to_server(f"save {filename}")
        return None
    result = self.game.save_game_to_file(filename)
    if result == 0:
        print(_("Game saved to {filename}.").format(filename=filename))
    else:
        print(_("Failed to save the game to {filename}.").format(
            filename=filename
        ))
    return result


def shuffle(self, client_service: IClientService) -> None:
    """Shuffle deck locally or request shuffle on server."""
    if client_service.connected_to_a_server():
        client_service.send_to_server("shuffle")
    else:
        seed = self.game.shuffle_deck()
        print(
            _("Deck shuffled. Algorithm: {algorithm}. Seed: {seed}").format(
                algorithm=self.game.game_data.shuffle_algo,
                seed=seed,
            )
        )


def draw(self, client_service: IClientService) -> None:
    """Draw one tile and print contextual feedback to the user."""
    if client_service.connected_to_a_server():
        client_service.send_to_server("draw")
    else:
        already_had_tile: bool = self.game.game_data.current_hand is not None
        tile = self.game.draw_tile()
        if tile is None:
            if getattr(
                self.game.game_data,
                "no_playable_tiles_remaining",
                False,
            ):
                print(
                    _(
                        "No playable move exists for the remaining tiles. "
                        "The game is over."
                    )
                )
                # Trigger the CLI end-of-game flow immediately so final
                # ranking and scores are displayed right away.
                on_game_over = getattr(self, "_on_game_over", None)
                if callable(on_game_over):
                    on_game_over()
            else:
                print(_("The deck is empty!"))
        elif already_had_tile:
            print(_("You already have a tile in hand."))
        else:
            print(_("Tile drawn: {tile}").format(tile=tile))


def hint(self, client_service) -> None:
    """Compute and print a local hint (or request one from server)."""
    if client_service.connected_to_a_server():
        client_service.send_to_server("hint")
        return
    from carcassonne.datas.serializer import parse_move
    move = self.game.provide_hint()
    if move:
        try:
            parsed = parse_move(move)
            description = _(
                "A good move is near tile {tile_id}."
            ).format(tile_id=parsed["target_id"])
            print(_("Hint: {description}").format(description=description))
        except Exception:
            print(_("Hint: play move {move}").format(move=move))
    else:
        print(_("No hint available."))


def undo(self, N, client_service: IClientService) -> None:
    """Undo one or multiple moves and report the result."""
    if N < 1:
        print(_("Usage: undo [N]"))
        return
    if client_service.connected_to_a_server():
        message = "undo" if N == 1 else f"undo {N}"
        client_service.send_to_server(message)
    else:
        undone = _apply_history_action(self.game, "undo", N)
        if undone == 0:
            print(_("No move to undo."))
        else:
            print(_("Last {count} move(s) undone.").format(count=N))


def redo(self, N, client_service: IClientService) -> None:
    """Redo one or multiple previously undone moves."""
    if N < 1:
        print(_("Usage: redo [N]"))
        return
    if client_service.connected_to_a_server():
        message = "redo" if N == 1 else f"redo {N}"
        client_service.send_to_server(message)
    else:
        redone = _apply_history_action(self.game, "redo", N)
        if redone == 0:
            print(_("No move to redo."))
        else:
            print(_("Last {count} move(s) redone.").format(count=N))


def show_hand(self, client_service: IClientService) -> None:
    """Display the tile currently in hand for the active local player."""
    if client_service.connected_to_a_server():
        client_service.send_to_server("show hand")
    else:
        if self.game.game_data.current_hand is None:
            print(_("No tile in hand."))
        else:
            print(
                _("Tile in hand: {tile}").format(
                    tile=self.game.game_data.current_hand
                )
            )


def _format_clock(remaining_seconds: float) -> str:
    """Format seconds as mm:ss."""
    minutes = int(remaining_seconds // 60)
    seconds = int(remaining_seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"


def show_time(self, player_id_raw: str | None = None) -> None:
    """Show blitz remaining time for all players or one player id."""
    if not self.game.get_game_configuration().get("blitz", False):
        print(_("Blitz mode is disabled."))
        return

    if player_id_raw is None or player_id_raw == "":
        players_times = self.game.get_all_players_remaining_time_seconds()
        if not players_times:
            print(_("Blitz mode is disabled."))
            return
        print(_("Remaining times:"))
        for player_id, remaining_seconds in players_times:
            print(
                _("- Player {player_id}: {clock}").format(
                    player_id=player_id,
                    clock=_format_clock(float(remaining_seconds)),
                )
            )
        return

    try:
        player_id = int(player_id_raw)
    except ValueError:
        print(_("Usage: show time [PLAYER_ID]"))
        return

    remaining_seconds = self.game.get_player_remaining_time_seconds(player_id)
    if remaining_seconds is None:
        print(_("Unknown player: {player_id}").format(player_id=player_id))
        return

    print(
        _("Remaining time for player {player_id}: {clock}").format(
            player_id=player_id,
            clock=_format_clock(float(remaining_seconds)),
        )
    )


def show_score(self, client_service: IClientService) -> None:
    """Display players scores in turn order (or ask server)."""
    if client_service.connected_to_a_server():
        client_service.send_to_server("show score")
        return

    print(_("Player scores:"))
    players = getattr(self.game.game_data, "players", {})
    players_order = self.game.get_players_order()
    if not players_order:
        players_order = list(players.keys())

    for player_id in players_order:
        player = players.get(player_id)
        if player is None:
            continue
        print(
            _("  {player}: {score} points").format(
                player=player.get_username(),
                score=player.get_score_int(),
            )
        )


def show_history(self, game, client_service: IClientService) -> None:
    """Print move history from local game or server."""
    if client_service.connected_to_a_server():
        client_service.send_to_server("show history")
    else:
        history = game.get_history()
        print(_("Move history:"))
        for move in history:
            print(f" {move}")


def show_configuration(self, game, client_service: IClientService) -> None:
    """Print active game configuration key/value pairs."""
    if client_service.connected_to_a_server():
        client_service.send_to_server("show configuration")
    else:
        config = game.get_game_configuration()
        print(_("Current game configuration:"))
        for key, value in config.items():
            print(f"  {key}: {value}")


def _print_board(game) -> None:
    """Print normalized board text ensuring final newline presence."""
    printed = game.get_printed_board()
    if not printed.endswith("\n"):
        printed += "\n"
    print(printed, end="")


def _print_scores(game) -> None:
    """Print per-player scores following current turn order."""
    print(_("Scores:"))
    players_order = game.get_players_order()
    for player_id in players_order:
        player = game.game_data.players[player_id]
        print(
            _("- Player {player_id}: {score} pts").format(
                player_id=player_id,
                score=player.get_score_int(),
            )
        )


def set_parameter(self, param, value, client_service: IClientService) -> None:
    """Set one configuration parameter locally or on the server."""
    if not param or value is None:
        print(_("Usage: set PARAM=VALUE"))
        return
    if client_service.connected_to_a_server():
        client_service.send_to_server(f"set {param}={value}")
    else:
        try:
            param, value = self.game.set_game_configuration(param, value)
        except KeyError as error:
            print(
                _("Invalid configuration parameter: {error}").format(
                    error=error.args[0]
                )
            )
            return
        except (TypeError, ValueError) as error:
            print(
                _("Invalid configuration parameter: {error}").format(
                    error=error
                )
            )
            return
        print(
            _("Parameter '{param}' set to '{value}'.").format(
                param=param,
                value=_display_value(value),
            )
        )


def play(self, move, game, client_service: IClientService) -> None:
    """Play one move, then process any immediate AI follow-up turns."""
    if client_service.connected_to_a_server():
        client_service.send_to_server(f"play {move}")
        return
    result = game.play_move(move)
    if not result:
        print(_("{move} failed.").format(move=move))
        _print_board(game)
        return
    if not game.is_undo_history_empty():
        game.clear_undo_history()
    _print_scores(game)
    _print_board(game)
    while game.get_current_player().is_ai_player():
        if game.end_game():
            break
        previous_player_id = game.get_current_player().get_id()
        game.play_ai_turn(game)
        _print_scores(game)
        _print_board(game)
        if game.end_game():
            break
        if game.get_current_player().get_id() == previous_player_id:
            break


def show_board(self, game, client_service: IClientService) -> None:
    """Display current board text locally or request it from server."""
    if client_service.connected_to_a_server():
        client_service.send_to_server("board")
    else:
        _print_board(game)


def show_server_list(self, client_service: IClientService):
    """Query and display currently discoverable online servers."""
    server_list = client_service.list_available_servers()
    print(_("Available servers list:"))
    for server in server_list:
        print(f"{server}:{server_list[server]}")


def server_start(self, port: str, server_service: IServerService):
    """Start local server on the provided port."""
    server_service.server_start(port)


def stop_server(self, server_service: IServerService):
    """Stop local server if running."""
    server_service.server_stop()


def join(
    self,
    client_service: IClientService,
    ip: str | None = None,
    port: str | None = None,
):
    """Join server using optional IP and port from command line."""
    if port is None and ip is None:
        client_service.join_server()
    if port is not None:
        client_service.join_server(ip, int(port))
    else:
        client_service.join_server(ip)


def ping(self, client_service: IClientService):
    """Send ping request to currently connected server."""
    client_service.send_to_server("ping")


def server_status(self, client_service: IClientService):
    """Request current server status string."""
    client_service.send_to_server("server status")


def players(self, client_service: IClientService, message: str):
    """Request player list/details from server."""
    client_service.send_to_server(message)


def scoreboard(self, client_service: IClientService):
    """Request scoreboard from server."""
    client_service.send_to_server("scoreboard")


def accept(self, client_service: IClientService):
    """Accept pending invitation on server."""
    client_service.send_to_server("accept")


def decline(self, client_service: IClientService):
    """Decline pending invitation on server."""
    client_service.send_to_server("decline")


def cancel(self, client_service: IClientService):
    """Cancel sent invitation(s) on server."""
    client_service.send_to_server("cancel")


def back(self, client_service: IClientService):
    """Set server-side user status to idle."""
    client_service.send_to_server("back")


def away(self, client_service: IClientService):
    """Set server-side user status to away."""
    client_service.send_to_server("away")
