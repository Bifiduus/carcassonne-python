"""Main file of the program"""
import argparse
import sys

from carcassonne import __version__
from carcassonne.BusinessLogic.Interfaces.IGamesRepository import IGamesRepository
from carcassonne.Datas.GamesRepository import GameRepository
from carcassonne.Presentation.Gui.CreateGui import CreateGui
from carcassonne.Presentation.Gui.Gui import GameGUI
from carcassonne.Presentation.Interfaces.IServerService import IServerService
from carcassonne.Presentation.Interfaces.IGameService import IGameService
from carcassonne.BusinessLogic.Game import Game
from carcassonne.BusinessLogic.Server import Server
from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData
from carcassonne.Presentation.Cli.Cli import GameCLI
from carcassonne.Datas.GraphData import GraphData


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str):  # pylint: disable=arguments-differ
        # Print error + help to stderr and exit with code 1.
        print(f"error: {message}", file=sys.stderr)
        self.print_help(sys.stderr)
        raise SystemExit(1)


def main() -> int:
    # pylint: disable=docstring-first-line-empty
    """
    Starting point of the program.
    """
    parser = ArgumentParser()
    parser.add_argument(
        "-V",
        "--version",
        help="display the version of the program",
        action="store_true",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help="increase verbosity",
        action="store_true",
    )
    parser.add_argument(
        "-d",
        "--debug",
        help="enable debug messages",
        action="store_true",
    )
    parser.add_argument(
        "-x",
        "--shuffle",
        metavar="SHUFFLE",
        help="algorithme de mélange (fisher-yates|naive)",
        choices=["fisher-yates", "naive"],
        default="fisher-yates",
    )
    parser.add_argument(
        "-s",
        "--seed",
        help="seed for shuffle randomness",
        type=int,
    )

    parser.add_argument(
        "-g",
        "--gui",
        help="enable GUI mode",
        action="store_true",
    )

    parser.add_argument(
        "-f",
        "--file",
        help="name of the file to load a game",
        type=str,
    )

    parser.add_argument(
        "-p",
        "--players",
        help="number of players (default: 2)",
        type=int,
    )

    args: argparse.Namespace = parser.parse_args()
    game_data: IGraphData = GraphData()
    if args.players:
        game: IGameService = Game(
            game_data, args.players if args.players > 1 and args.players <= 5 else 2)
    else:
        game: IGameService = Game(game_data, 1)
    game_repo: IGamesRepository = GameRepository()
    server_service: IServerService = Server(game_repo)
    game.shuffle_algo = args.shuffle
    game.default_seed = args.seed
    if args.version:
        print(f"Carcassonne: version {__version__}")
    if args.debug:
        print("Debug mode enabled.", file=sys.stderr)
    if args.file:
        print(f"Loading game from file: {args.file}")
    if args.verbose:
        print("Verbose mode enabled.")
    if args.gui:
        print("GUI mode enabled.")
        CreateGui(game)
    else:
        game_cli = GameCLI(game, server_service)
        game_cli.run()

    # Call a function to start the game

    return 0
