"""This module defines the GameCLI class, which provides a command-line interface for interacting with the Carcassonne game.
The GameCLI class allows players to enter commands to perform various actions such as starting a new game, 
loading and saving game states, shuffling the tiles, getting hints, undoing and redoing moves, 
and displaying game information such as the player's hand, scores, history, and configuration.
"""
from carcassonne.presentation.interfaces.i_game_service import IGameService
from carcassonne.presentation.cli import commands_handler_cli
from carcassonne.business_logic.game import Game

import readline
import os
import atexit
from pathlib import Path

COMMANDS = [
    "new", "help", "quit", "load", "save",
    "shuffle", "draw", "hint", "undo", "redo",
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
        self.settings = self.game.get_game_configuration()
        self.running = True

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

        if command.startswith("new"):
            args = command[4:].strip()
            commands_handler_cli.new_game(self, args)
        elif command == "help":
            commands_handler_cli.help(self)
        elif command == "quit":
            commands_handler_cli.quit(self)
        elif command.startswith("load "):
            filename = command[5:].strip()
            commands_handler_cli.load(self, filename)
        elif command.startswith("save "):
            filename = command[5:].strip()
            commands_handler_cli.save(self, filename)
        elif command == "shuffle":
            commands_handler_cli.shuffle(self)
        elif command == "draw":
            commands_handler_cli.draw(self)
        elif command == "hint":
            commands_handler_cli.hint(self)
        elif command == "undo":
            commands_handler_cli.undo(self, 1)
        elif command == "redo":
            commands_handler_cli.redo(self, 1)
        elif command == "show hand":
            commands_handler_cli.show_hand(self)
        elif command == "show score":
            commands_handler_cli.show_score(self)
        elif command == "show history":
            commands_handler_cli.show_history(self, game=self.game)
        elif command == "show configuration":
            commands_handler_cli.show_configuration(self, game=self.game)
        elif command.startswith("set"):
            content = command[3:].strip()
            if "=" in content:
                param, value = content.split("=", 1)
                param = param.strip()
                value = value.strip()
            else:
                param = content
                value = None
            commands_handler_cli.set_parameter(self, param, value)
        elif command.startswith("play"):
            move = command[5:].strip()
            commands_handler_cli.play(self, move, game=self.game)
        elif command.startswith("board"):
            commands_handler_cli.show_board(self, game=self.game)

        else:
            print("Commande inconnue. Tapez 'help' pour la liste des commandes.")
