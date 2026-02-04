from carcassonne.IGameService import IGameService
from carcassonne.Présentation import CommandsHandler

import readline
import os
import atexit
from pathlib import Path



class GameCLI:
    def __init__(self, game):
        self.game = game
        self.running = True
        """HISTORY_FILE = os.path.expanduser("~/.carcassonne_history")

        try:
            readline.read_history_file(HISTORY_FILE)
            print(HISTORY_FILE)
            print("Previous command history loaded.")
        except FileNotFoundError:
            print("No previous history file found.")

        atexit.register(readline.write_history_file, HISTORY_FILE)"""

    def run(self):
        print("Bienvenue dans Carcassonne")
        print("Tapez 'help' pour la liste des commandes.\n")

        while self.running:
            try:
                texte = input("> ").strip()
                self.handle_command(self, texte, self.game.current_player)
            except KeyboardInterrupt:
                print("\nFin de partie.")
                self.running = False

    def handle_command(self, command, player):
        
        if command == "help":
            self.show_help()
        elif command == "status":
            self.show_status(player)
        elif command.startswith("place "):
            self.p(command[6:], player)
        elif command.startswith("meeple "):
            self.place_meeple(command[7:], player)
        elif command == "end":
            self.end_turn(player)
        else:
            print("Commande inconnue. Tapez 'help' pour la liste des commandes.")
        def show_help(self):
            print("Commandes disponibles:")
            print("  help          - Affiche cette aide")
            print("  status        - Affiche le statut actuel du jeu")
            print("  place <args>  - Place une tuile avec les arguments spécifiés")
            print("  meeple <args> - Place un meeple avec les arguments spécifiés")
            print("  end           - Termine le tour actuel")