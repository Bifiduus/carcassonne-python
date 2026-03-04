"""This module defines the command handler functions for the Carcassonne game.
Each function corresponds to a specific command that can be entered by the player in the command-line interface. 
The functions interact with the game service and the game state to perform actions such as starting a new game, loading and saving game states, 
shuffling the tiles, providing hints, undoing and redoing moves, and displaying game information. 
The command handler functions are designed to be called from the GameCLI class when the corresponding commands are entered by the player.
"""
from carcassonne.Presentation.Interfaces.IGameService import IGameService


def new_game(self, args):
        self.game.start_new_game()
        print("Nouvelle partie commencée.")

def help(self):
    print("Commandes disponibles:")
    print("  new <args>         - Démarre une nouvelle partie")
    print("  help               - Affiche cette aide")
    print("  quit               - Quitte le jeu")
    print("  load <file>        - Charge une partie depuis un fichier")
    print("  save <file>        - Sauvegarde la partie dans un fichier")
    print("  shuffle            - Mélange les tuiles de la pioche")
    print("  draw               - Pioche une tuile")
    print("  hint               - Donne un indice pour le placement de la tuile")
    print("  undo [N]           - Annule le dernier coup ou les N derniers coups")
    print("  redo [N]           - Rétablit le dernier coup annulé ou les N derniers coups annulés")
    print("  show hand          - Affiche la main du joueur courant")
    print("  show score         - Affiche le score des joueurs")
    print("  show history       - Affiche l'historique des coups joués")
    print("  show configuration - Affiche la configuration actuelle du jeu")
    print("  set (PARAM=VALUE)  - Définit un paramètre de configuration")
    print("  play <move>        - Joue le coup spécifié par <move>")

def quit(self):
        saved = -1
        while saved == -1:
                confirm = input("Save the game before quitting?[y/N] ")
                if confirm != 'y':
                        print("Abandon de la commande de quitter.")
                        self.running = False
                        saved = 0
                else:
                        filename = input("Nom du fichier de sauvegarde: ")
                        saved = save(self, filename)
        print("Quitte le jeu. À bientôt!")
        self.running = False

def load(self, filename):
        if self.game.load_game_from_file(filename) == 0:
            print(f"Partie chargée depuis {filename}.")
        else:
            print(f"Erreur lors du chargement de la partie depuis {filename}.")

def save(self, filename):
        if self.game.save_game_to_file(filename) == 0:
            print(f"Partie sauvegardée dans {filename}.")

def shuffle(self):
        seed = self.game.shuffle_deck()
        print(f"Pioche mélangée. Algo: {self.game.shuffle_algo}. Seed: {seed}")

def draw(self):
        already_had_tile = self.game.current_hand is not None
        tile = self.game.draw_tile()
        if tile is None:
            print("La pioche est vide!")
        elif already_had_tile:
            print("Vous avez déjà une tuile en main.")
        else:
            print(f"Tuile piochée: {tile}")

    
def hint(self):
        #hint = self.game.getPlacementHint()
        print(f"Indice pour le placement de la tuile: ")

def undo(self, N):
        self.game.undo()
        print(f"Derniers {N} coups annulés.")

def redo(self, N):
        self.game.redo()
        print(f"Derniers {N} coups rétablis.")

def show_hand(self):
        if self.game.current_hand is None:
            print("Aucune tuile en main.")
        else:
            print(f"Tuile en main: {self.game.current_hand}")

def show_score(self):
        #scores = self.game.getPlayerScores()
        print("Scores des joueurs:")
        #for player, score in scores.items():
        #    print(f"  {player}: {score}")

def show_history(self, game):
        history = game.get_history()
        print("Historique des coups joués:")
        for move in history:
            print(f" {move}")

def show_configuration(self, game):
        config = game.get_game_configuration()
        print("Configuration actuelle du jeu:")
        for key, value in config.items():
            print(f"  {key}: {value}")

    
def set_parameter(self, param, value):
        #self.game.setGameParameter(param, value)
        print(f"Paramètre '{param}' défini à '{value}'.")
        
def play(self, move, game):
        result = game.play_move(move)
        game.get_board()
        if not game.is_undo_history_empty():
                game.clear_undo_history()
        if result:
                while game.get_current_player().is_ai_player():
                        game.play_ai_turn()
                        game.get_board()

def show_board(self, game):
        game.get_board()
