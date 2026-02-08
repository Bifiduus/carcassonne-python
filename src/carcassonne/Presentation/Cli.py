from carcassonne.Presentation.Interfaces.IGameService import IGameService
from carcassonne.Presentation import CommandsHandler
from carcassonne.BusinessLogic.Game import Game

import readline
import os
import atexit
from pathlib import Path

COMMANDS = [
    "new", "help", "quit", "load", "save",
    "shuffle", "hint", "undo", "redo",
    "show hand", "show score", "show history", "show configuration",
    "set"
    ]

def completer(texte, state):

        # filtrer les commandes qui commencent par text
        matches = [cmd for cmd in COMMANDS if cmd.startswith(texte)]
        if state < len(matches):
            return matches[state]
        else:
            return None
class GameCLI:
    
    
    def __init__(self, game_service: IGameService):
        self.game = game_service
        self.running = True
        """HISTORY_FILE = os.path.expanduser("~/.carcassonne_history")

        try:
            readline.read_history_file(HISTORY_FILE)
            print(HISTORY_FILE)
            print("Previous command history loaded.")
        except FileNotFoundError:
            print("No previous history file found.")

        atexit.register(readline.write_history_file, HISTORY_FILE)"""

        
        readline.set_completer(completer)
        readline.parse_and_bind("tab: complete") 

        readline.parse_and_bind("set show-all-if-ambiguous on")

    def run(self):
        print("Bienvenue dans Carcassonne")
        print("Tapez 'help' pour la liste des commandes.\n")

        while self.running:
            try:
                command = input(">> ").strip()
                self.handle_command(command)
            except KeyboardInterrupt:
                print("\nFin de partie.")
                self.running = False

    def handle_command(self, command):

        if command.startswith("new "):
            args = command[4:].strip()
            CommandsHandler.new_game(self, args)
        elif command == "help":
            CommandsHandler.help(self)
        elif command == "quit":
            CommandsHandler.quit(self)
        elif command.startswith("load "):   
            filename = command[5:].strip()
            CommandsHandler.load(self, filename)
        elif command.startswith("save "):
            filename = command[5:].strip()
            CommandsHandler.save(self, filename)
        elif command == "shuffle":
            CommandsHandler.shuffle(self)
        elif command == "hint":
            CommandsHandler.hint(self)
        elif command == "undo":
            CommandsHandler.undo(self, 1)
        elif command == "redo":
            CommandsHandler.redo(self, 1)
        elif command == "show hand":
            CommandsHandler.show_hand(self)
        elif command == "show score":
            CommandsHandler.show_score(self)
        elif command == "show history":
            CommandsHandler.show_history(self, game=self.game)
        elif command == "show configuration":
            CommandsHandler.show_configuration(self, game=self.game)
        elif command.startswith("set "):
            content = command[4:].strip()
            if "=" in content:
                param, value = content.split("=", 1)
                param = param.strip()
                value = value.strip()
            else:
                param = content
                value = None
            CommandsHandler.set_parameter(self, param, value)
        elif command.startswith("play"):
            move = command[5:].strip()
            CommandsHandler.play(self, move, game=self.game)


        else:
            print("Commande inconnue. Tapez 'help' pour la liste des commandes.")

    