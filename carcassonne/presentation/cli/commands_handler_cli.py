"""This module defines the command handler functions for the Carcassonne game.
Each function corresponds to a specific command that can be entered by the
 player in the command-line interface.
The functions interact with the game service and the game state to perform
 actions such as starting a new game, loading and saving game states,
shuffling the tiles, providing hints, undoing and redoing moves,
 and displaying game information.
The command handler functions are designed to be called from the GameCLI class
 when the corresponding commands are entered by the player.
"""

from carcassonne.presentation.interfaces.i_client_service import IClientService
from carcassonne.i18n import gettext as _
from carcassonne.presentation.interfaces.i_server_service import IServerService


def new_game(self, args, client_service: IClientService) -> None:
    if client_service.connected_to_a_server():
        client_service.send_to_server("new " + args)
        return
    self.game.start_new_game()
    print(_("New game started."))


def help(self) -> None:
    print(_("Available commands:"))
    print(_("  new <args>         - Start a new game"))
    print(_("  help               - Display this help message"))
    print(_("  quit               - Quit the game"))
    print(_("  load <file>        - Load a game from a file"))
    print(_("  save <file>        - Save the game to a file"))
    print(_("  shuffle            - Shuffle the deck"))
    print(_("  draw               - Draw a tile"))
    print(_("  hint               - Show a hint for the current tile"))
    print(
        _("  undo [N]           - Undo the last move or the last N moves")
    )
    print(
        _(
            "  redo [N]           - Redo the last undone move or the last "
            "N undone moves"
        )
    )
    print(_("  show hand          - Display the current player's hand"))
    print(
        _(
            "  show time [ID]     - Display the remaining time of all "
            "players or of player ID"
        )
    )
    print(_("  show score         - Display the players' scores"))
    print(_("  show history       - Display the move history"))
    print(_("  show configuration - Display the current game configuration"))
    print(_("  set (PARAM=VALUE)  - Set a configuration parameter"))
    print(_("  play <move>        - Play the specified move"))
    print(_("  server start [PORT] - Start the server on port [PORT]"))
    print(_("  server list        - Display the list of available servers"))
    print(_("  server stop        - Stop the server"))
    print(
        _(
            "  join [IP[:PORT]]   - Connect the client to the given server "
            "or to its own server"
        )
    )
    print(_("  quit               - Quit the server"))
    print(_("  ping               - Display the server ping"))
    print(_("  server status      - Display the server status"))
    print(
        _(
            "  players [PLAYER_ID] - Display connected players or "
            "information about player [PLAYER_ID]"
        )
    )
    print(_("  scoreboard         - Display the server scoreboard"))
    print(
        _("  new PLAYER_ID ..   - Start a game with the proposed players")
    )
    print(_("  accept             - Accept the received invitation"))
    print(_("  decline            - Decline the received invitation"))
    print(_("  cancel             - Cancel the sent invitation"))
    print(_('  away               - Change the status to "away"'))
    print(_('  back               - Change the status to "idle"'))


def quit(
    self, server_service: IServerService, client_service: IClientService
) -> None:
    if client_service.connected_to_a_server():
        client_service.send_to_server("quit")
        return
    if server_service.is_server_running():
        print(_("You should close your server first."))
        return
    else:
        saved: int | None = -1
        while saved == -1:
            confirm: str = input(_("Save the game before quitting? [y/N] "))
            if confirm != "y":
                print(_("Quit command aborted."))
                self.running = False
                saved = 0
            else:
                filename: str = input(_("Save file name: "))
                saved: None = save(self, filename, client_service)
        print(_("Quitting the game. See you soon!"))
        self.running = False


def load(self, filename, client_service: IClientService) -> None:
    if client_service.connected_to_a_server():
        client_service.send_to_server(f"load {filename}")
    else:
        if self.game.load_game_from_file(filename) == 0:
            print(_("Game loaded from {filename}.").format(filename=filename))
        else:
            print(
                _("Failed to load the game from {filename}.").format(
                    filename=filename
                )
            )


def save(self, filename, client_service: IClientService) -> None:
    if client_service.connected_to_a_server():
        client_service.send_to_server(f"save {filename}")
    else:
        if self.game.save_game_to_file(filename) == 0:
            print(_("Game saved to {filename}.").format(filename=filename))


def shuffle(self, client_service: IClientService) -> None:
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
    if client_service.connected_to_a_server():
        client_service.send_to_server("draw")
    else:
        already_had_tile: bool = self.game.game_data.current_hand is not None
        tile = self.game.draw_tile()
        if tile is None:
            print("La pioche est vide!")
        elif already_had_tile:
            print("Vous avez déjà une tuile en main.")
        else:
            print(f"Tuile piochée: {tile}")


def hint(self, client_service) -> None:
    if client_service.connected_to_a_server():
        client_service.send_to_server("hint")
        return
    from carcassonne.datas.serializer import parse_move
    move = self.game.provide_hint()
    if move:
        try:
            parsed = parse_move(move)
            description = (
                f"Placez la tuile à la position {parsed['target_id']} "
                f"sur le côté {parsed['target_side']}, tournée de "
                f"{parsed['rotation'] * 90} degrés."
            )
            if parsed['meeple']:
                description += f" et placez un meeple sur {parsed['meeple']}."
            print(f"Conseil: {description}")
        except Exception:
            print(f"Conseil: Jouez le coup {move}")
    else:
        print("Aucun conseil disponible.")


def undo(self, N, client_service: IClientService) -> None:
    if client_service.connected_to_a_server():
        client_service.send_to_server("undo")
    else:
        self.game.undo()
        print(_("Last {count} move(s) undone.").format(count=N))


def redo(self, N, client_service: IClientService) -> None:
    if client_service.connected_to_a_server():
        client_service.send_to_server("redo")
    else:
        self.game.redo()
        print(_("Last {count} move(s) redone.").format(count=N))


def show_hand(self, client_service: IClientService) -> None:
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
    minutes = int(remaining_seconds // 60)
    seconds = int(remaining_seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"


def show_time(self, player_id_raw: str | None = None) -> None:
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
    # scores = self.game.getPlayerScores()
    print(_("Player scores:"))
    # for player, score in scores.items():
    #    print(f"  {player}: {score}")


def show_history(self, game, client_service: IClientService) -> None:
    if client_service.connected_to_a_server():
        client_service.send_to_server("show history")
    else:
        history = game.get_history()
        print(_("Move history:"))
        for move in history:
            print(f" {move}")


def show_configuration(self, game, client_service: IClientService) -> None:
    if client_service.connected_to_a_server():
        client_service.send_to_server("show configuration")
    else:
        config = game.get_game_configuration()
        print(_("Current game configuration:"))
        for key, value in config.items():
            print(f"  {key}: {value}")


def set_parameter(self, param, value, client_service: IClientService) -> None:
    if client_service.connected_to_a_server():
        client_service.send_to_server(f"set {param}={value}")
    else:
        # self.game.setGameParameter(param, value)
        print(
            _("Parameter '{param}' set to '{value}'.").format(
                param=param,
                value=value,
            )
        )


def play(self, move, game, client_service: IClientService) -> None:
    if client_service.connected_to_a_server():
        client_service.send_to_server(f"play {move}")
        return
    result = game.play_move(move)
    game.get_board()
    if not game.is_undo_history_empty():
        game.clear_undo_history()
    if result:
        while game.get_current_player().is_ai_player():
            if game.end_game():
                break
            previous_player_id = game.get_current_player().get_id()
            game.play_ai_turn(game)
            game.get_board()
            if game.end_game():
                break
            if game.get_current_player().get_id() == previous_player_id:
                break


def show_board(self, game, client_service: IClientService) -> None:
    if client_service.connected_to_a_server():
        client_service.send_to_server("board")
    else:
        game.get_board()


def show_server_list(self, client_service: IClientService):
    server_list = client_service.list_available_servers()
    print(_("Available servers list:"))
    for server in server_list:
        print(f"{server}:{server_list[server]}")


def server_start(self, port: str, server_service: IServerService):
    server_service.server_start(port)


def stop_server(self, server_service: IServerService):
    server_service.server_stop()


def join(
    self,
    client_service: IClientService,
    ip: str | None = None,
    port: str | None = None,
):
    if port is None and ip is None:
        client_service.join_server()
    if port is not None:
        client_service.join_server(ip, int(port))
    else:
        client_service.join_server(ip)


def ping(self, client_service: IClientService):
    print(client_service.ping())


def server_status(self, client_service: IClientService):
    client_service.send_to_server("server status")


def players(self, client_service: IClientService, message: str):
    client_service.send_to_server(message)


def scoreboard(self, client_service: IClientService):
    client_service.send_to_server("scoreboard")


def accept(self, client_service: IClientService):
    client_service.send_to_server("accept")


def decline(self, client_service: IClientService):
    client_service.send_to_server("decline")


def cancel(self, client_service: IClientService):
    client_service.send_to_server("cancel")


def back(self, client_service: IClientService):
    client_service.send_to_server("back")


def away(self, client_service: IClientService):
    client_service.send_to_server("away")
