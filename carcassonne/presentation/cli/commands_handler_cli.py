"""This module defines the command handler functions for the Carcassonne game.
Each function corresponds to a specific command that can be entered by the player in the command-line interface.
The functions interact with the game service and the game state to perform actions such as starting a new game, loading and saving game states,
shuffling the tiles, providing hints, undoing and redoing moves, and displaying game information.
The command handler functions are designed to be called from the GameCLI class when the corresponding commands are entered by the player.
"""

from carcassonne.presentation.interfaces.i_game_service import IGameService
from carcassonne.presentation.interfaces.i_server_service import IServerService


def new_game(self, args, server_service: IServerService) -> None:
    if server_service.connected_to_a_server():
        server_service.send_to_server("new "+args)
    self.game.start_new_game()
    print("Nouvelle partie commencée.")


def help(self) -> None:
    print("Commandes disponibles:")
    print("  new <args>         - Démarre une nouvelle partie")
    print("  help               - Affiche cette aide")
    print("  quit               - Quitte le jeu")
    print("  load <file>        - Charge une partie depuis un fichier")
    print("  save <file>        - Sauvegarde la partie dans un fichier")
    print("  shuffle            - Mélange les tuiles de la pioche")
    print("  draw               - Pioche une tuile")
    print(
        "  hint               - Donne un indice pour le placement de la tuile"
    )
    print(
        "  undo [N]           - Annule le dernier coup ou les N derniers coups"
    )
    print(
        "  redo [N]           - Rétablit le dernier coup annulé ou les "
        "N derniers coups annulés"
    )
    print("  show hand          - Affiche la main du joueur courant")
    print(
        "  show time [ID]     - Affiche le temps restant de tous les "
        "joueurs ou du joueur ID"
    )
    print("  show score         - Affiche le score des joueurs")
    print("  show history       - Affiche l'historique des coups joués")
    print("  show configuration - Affiche la configuration actuelle du jeu")
    print("  set (PARAM=VALUE)  - Définit un paramètre de configuration")
    print("  play <move>        - Joue le coup spécifié par <move>")


def quit(self, server_service: IServerService) -> None:
    if server_service.connected_to_a_server():
        server_service.send_to_server("quit")
    else:
        saved = -1
        while saved == -1:
            confirm: str = input("Save the game before quitting?[y/N] ")
            if confirm != 'y':
                print("Abandon de la commande de quitter.")
                self.running = False
                saved = 0
            else:
                filename: str = input("Nom du fichier de sauvegarde: ")
                saved: None = save(self, filename)
        print("Quitte le jeu. À bientôt!")
        self.running = False


def load(self, filename) -> None:
    if self.game.load_game_from_file(filename) == 0:
        print(f"Partie chargée depuis {filename}.")
    else:
        print(f"Erreur lors du chargement de la partie depuis {filename}.")


def save(self, filename) -> None:
    if self.game.save_game_to_file(filename) == 0:
        print(f"Partie sauvegardée dans {filename}.")


def shuffle(self) -> None:
    seed = self.game.shuffle_deck()
    print(f"Pioche mélangée. Algo: {self.game.shuffle_algo}. Seed: {seed}")


def draw(self) -> None:
    already_had_tile: bool = self.game.current_hand is not None
    tile = self.game.draw_tile()
    if tile is None:
        print("La pioche est vide!")
    elif already_had_tile:
        print("Vous avez déjà une tuile en main.")
    else:
        print(f"Tuile piochée: {tile}")


def hint(self) -> None:
    # hint = self.game.getPlacementHint()
    print(f"Indice pour le placement de la tuile: ")


def undo(self, N) -> None:
    self.game.undo()
    print(f"Derniers {N} coups annulés.")


def redo(self, N) -> None:
    self.game.redo()
    print(f"Derniers {N} coups rétablis.")


def show_hand(self) -> None:
    if self.game.current_hand is None:
        print("Aucune tuile en main.")
    else:
        print(f"Tuile en main: {self.game.current_hand}")


def _format_clock(remaining_seconds: float) -> str:
    minutes = int(remaining_seconds // 60)
    seconds = int(remaining_seconds % 60)
    return f"{minutes:02d}:{seconds:02d}"


def show_time(self, player_id_raw: str | None = None) -> None:
    if not self.game.get_game_configuration().get("blitz", False):
        print("Mode blitz désactivé.")
        return

    if player_id_raw is None or player_id_raw == "":
        players_times = self.game.get_all_players_remaining_time_seconds()
        if not players_times:
            print("Mode blitz désactivé.")
            return
        print("Temps restants:")
        for player_id, remaining_seconds in players_times:
            print(
                f"- Joueur {player_id}: "
                f"{_format_clock(float(remaining_seconds))}"
            )
        return

    try:
        player_id = int(player_id_raw)
    except ValueError:
        print("Usage: show time [PLAYER_ID]")
        return

    remaining_seconds = self.game.get_player_remaining_time_seconds(player_id)
    if remaining_seconds is None:
        print(f"Joueur inconnu: {player_id}")
        return

    print(
        f"Temps restant joueur {player_id}: "
        f"{_format_clock(float(remaining_seconds))}"
    )


def show_score(self) -> None:
    # scores = self.game.getPlayerScores()
    print("Scores des joueurs:")
    # for player, score in scores.items():
    #    print(f"  {player}: {score}")


def show_history(self, game) -> None:
    history = game.get_history()
    print("Historique des coups joués:")
    for move in history:
        print(f" {move}")


def show_configuration(self, game) -> None:
    config = game.get_game_configuration()
    print("Configuration actuelle du jeu:")
    for key, value in config.items():
        print(f"  {key}: {value}")


def set_parameter(self, param, value) -> None:
    # self.game.setGameParameter(param, value)
    print(f"Paramètre '{param}' défini à '{value}'.")


def create(self, username: str, server_service: IServerService):
    answer = server_service.create_online_player(username)
    print(answer)


def play(self, move, game) -> None:
    result = game.play_move(move)
    game.get_board()
    if not game.is_undo_history_empty():
        game.clear_undo_history()
    if result:
        while game.get_current_player().is_ai_player():
            if game.end_game():
                break
            previous_player_id = game.get_current_player().get_id()
            game.play_ai_turn()
            game.get_board()
            if game.end_game():
                break
            if game.get_current_player().get_id() == previous_player_id:
                break


def show_board(self, game) -> None:
    game.get_board()


def show_server_list(self, server_service: IServerService):
    server_list = server_service.list_available_servers()
    print("Available servers list:")
    for server in server_list:
        print(server)


def server_start(self, port: str, server_service: IServerService):
    server_service.server_start(port)


def stop_server(self, server_service: IServerService):
    server_service.server_stop()


def join(self, server_service: IServerService, ip: str | None = None, port: str | None = None):
    if port is None and ip is None:
        server_service.join_server()
    if port is not None:
        server_service.join_server(ip, int(port))
    else:
        server_service.join_server(ip)


def ping(self, server_service: IServerService):
    print(server_service.ping())


def server_status(self, server_service: IServerService):
    server_service.send_to_server("server status")


def players(self, server_service: IServerService, message: str):
    server_service.send_to_server(message)


def scoreboard(self, server_service: IServerService):
    server_service.send_to_server("scoreboard")


def accept(self, server_service: IServerService):
    server_service.send_to_server("accept")


def decline(self, server_service: IServerService):
    server_service.send_to_server("decline")


def cancel(self, server_service: IServerService):
    server_service.send_to_server("cancel")


def back(self, server_service: IServerService):
    server_service.send_to_server("back")


def away(self, server_service: IServerService):
    server_service.send_to_server("away")
