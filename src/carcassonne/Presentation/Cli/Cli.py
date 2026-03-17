"""This module defines the GameCLI class, which provides a command-line interface for interacting with the Carcassonne game.
The GameCLI class allows players to enter commands to perform various actions such as starting a new game, 
loading and saving game states, shuffling the tiles, getting hints, undoing and redoing moves, 
and displaying game information such as the player's hand, scores, history, and configuration.
"""
from carcassonne.Presentation.GameConfiguration import GameConfiguration
from carcassonne.Presentation.Interfaces.IGameService import IGameService
from carcassonne.Presentation.Cli import CommandsHandlerCli
from carcassonne.BusinessLogic.Game import Game

import readline
import os
import atexit
from pathlib import Path

from carcassonne.Presentation.Interfaces.IServerService import IServerService

COMMANDS = [
    "new", "help", "quit", "load", "save",
    "shuffle", "draw", "hint", "undo", "redo",
    "show hand", "show score", "show history", "show configuration",
    "set", "server list", "server start", "server stop", "join",
    "ping"
]


def completer(texte, state):

    # filtrer les commandes qui commencent par text
    matches = [cmd for cmd in COMMANDS if cmd.startswith(texte)]
    if state < len(matches):
        return matches[state]
    else:
        return None


class GameCLI:

    def __init__(self, game_service: IGameService, server_service: IServerService):
        self.game = game_service
        self.server = server_service
        self.settings = GameConfiguration().settings
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
            CommandsHandlerCli.new_game(self, args, self.server)
        elif command == "help":
            CommandsHandlerCli.help(self)
        elif command == "quit":
            CommandsHandlerCli.quit(self, self.server)
        elif command.startswith("load "):
            filename = command[5:].strip()
            CommandsHandlerCli.load(self, filename)
        elif command.startswith("save "):
            filename = command[5:].strip()
            CommandsHandlerCli.save(self, filename)
        elif command == "shuffle":
            CommandsHandlerCli.shuffle(self)
        elif command == "draw":
            CommandsHandlerCli.draw(self)
        elif command == "hint":
            CommandsHandlerCli.hint(self)
        elif command == "undo":
            CommandsHandlerCli.undo(self, 1)
        elif command == "redo":
            CommandsHandlerCli.redo(self, 1)
        elif command == "show hand":
            CommandsHandlerCli.show_hand(self)
        elif command == "show score":
            CommandsHandlerCli.show_score(self)
        elif command == "show history":
            CommandsHandlerCli.show_history(self, game=self.game)
        elif command == "show configuration":
            CommandsHandlerCli.show_configuration(self, game=self.game)
        elif command.startswith("set"):
            content = command[3:].strip()
            if "=" in content:
                param, value = content.split("=", 1)
                param = param.strip()
                value = value.strip()
            else:
                param = content
                value = None
            CommandsHandlerCli.set_parameter(self, param, value)
        elif command.startswith("play "):
            move = command[5:].strip()
            CommandsHandlerCli.play(self, move, game=self.game)
        elif command.startswith("board"):
            CommandsHandlerCli.show_board(self, game=self.game)
        elif command == "server list":
            CommandsHandlerCli.show_server_list(self, self.server)
        elif command.startswith("server start"):
            port = command.strip("server start")
            CommandsHandlerCli.server_start(self, port, self.server)
        elif command == "server stop":
            CommandsHandlerCli.stop_server(self, self.server)
        elif command.startswith("join"):
            addresse = command[5:].strip()
            if ":" in addresse:
                ip, port = addresse.split(":")
                CommandsHandlerCli.join(self, self.server, ip, port)
            else:
                CommandsHandlerCli.join(self, self.server, addresse)
        elif command == "ping":
            CommandsHandlerCli.ping(self, self.server)
        elif command.startswith("create"):
            command = command[7:].strip()
            CommandsHandlerCli.create(self, command, self.server)
        elif command == "server status":
            CommandsHandlerCli.server_status(self, self.server)
        elif command.startswith("players"):
            CommandsHandlerCli.players(self, self.server, command)
        elif command == "scoreboard":
            CommandsHandlerCli.scoreboard(self, self.server)
        elif command == "accept":
            CommandsHandlerCli.accept(self, self.server)
        elif command == "decline":
            CommandsHandlerCli.decline(self, self.server)
        elif command == "cancel":
            CommandsHandlerCli.cancel(self, self.server)
        elif command == "back":
            CommandsHandlerCli.back(self, self.server)
        elif command == "away":
            CommandsHandlerCli.away(self, self.server)
        else:
            print("Commande inconnue. Tapez 'help' pour la liste des commandes.")
