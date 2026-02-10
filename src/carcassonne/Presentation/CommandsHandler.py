
from carcassonne.Presentation.Interfaces.IGameService import IGameService


def new_game(self, args):
        #self.game.startNewGame()
        print("Nouvelle partie commencée.")

def help(self):
    print("Commandes disponibles:")
    print("  new <args>         - Démarre une nouvelle partie")
    print("  help               - Affiche cette aide")
    print("  quit               - Quitte le jeu")
    print("  load <file>        - Charge une partie depuis un fichier")
    print("  save <file>        - Sauvegarde la partie dans un fichier")
    print("  shuffle            - Mélange les tuiles de la pioche")
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
        print("Quitte le jeu. À bientôt!")
        self.running = False

def load(self, filename):
        #self.game.loadGameFromFile(filename)
        print(f"Partie chargée depuis {filename}.")

def save(self, filename):
        #self.game.saveGameToFile(filename)
        print(f"Partie sauvegardée dans {filename}.")

def shuffle(self):
        #self.game.shuffleDeck()
        print("Pioche mélangée.")
    
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
        #hand = self.game.getCurrentPlayerHand()
        print("Main du joueur courant:")

def show_score(self):
        #scores = self.game.getPlayerScores()
        print("Scores des joueurs:")
        #for player, score in scores.items():
        #    print(f"  {player}: {score}")

def show_history(self, game):
        history = game.get_history()
        print("Historique des coups joués:")
        for move in history:
            print(f"  {move.move_str}")

def show_configuration(self, game):
        grid = game.get_game_configuration()
        print("Configuration actuelle du jeu:")
        # Affichez la configuration du jeu (par exemple, les tuiles sur le plateau)
        for pos, tile in grid.items():
            print(f"  Position {pos}: {tile['name']} (orientation: {tile['orientation']}, neighbors: {tile['neighbors']})")

    
def set_parameter(self, param, value):
        #self.game.setGameParameter(param, value)
        print(f"Paramètre '{param}' défini à '{value}'.")
        
def play(self, move, game):
        game.play_move(move)
        if not game.is_undo_history_empty():
                game.clear_undo_history()


def show_board(self, game):
        game.get_board()

