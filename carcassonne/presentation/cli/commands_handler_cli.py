"""This module defines the command handler functions for the Carcassonne game.
Each function corresponds to a specific command entered in the CLI.
The handlers call the game service to start/load/save games, draw and place
tiles, provide hints, undo/redo, and display game information.
"""

from carcassonne.presentation.interfaces.i_game_service import IGameService


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
    print("  show score         - Affiche le score des joueurs")
    print("  show history       - Affiche l'historique des coups joués")
    print("  show configuration - Affiche la configuration actuelle du jeu")
    print("  set (PARAM=VALUE)  - Définit un paramètre de configuration")
    print("  play <move>        - Joue le coup spécifié par <move>")


def quit(self) -> None:
    saved = -1
    while saved == -1:
        confirm: str = input("Save the game before quitting?[y/N] ")
        if confirm != "y":
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
            game.play_ai_turn()
            game.get_board()


def show_board(self, game) -> None:
    game.get_board()
