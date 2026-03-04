"""Main file of the program"""
import argparse
import sys

from carcassonne import __version__
from carcassonne.Presentation.Gui.CreateGui import CreateGui
from carcassonne.Presentation.Gui.Gui import GameGUI
from carcassonne.Presentation.Interfaces.IGameService import IGameService
from carcassonne.BusinessLogic.Game import Game
from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData
from carcassonne.Presentation.Cli.Cli import GameCLI
from carcassonne.Datas.GraphData import GraphData

class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):  # pylint: disable=arguments-differ
        # Print error + help to stderr and exit with code 1.
        print(f"error: {message}", file=sys.stderr)
        self.print_help(sys.stderr)
        raise SystemExit(1)


def main():
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
    args = parser.parse_args()
    game_data :IGraphData = GraphData()
    game :IGameService = Game(game_data)
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
        game_cli = GameCLI(game)
        game_cli.run()


    # Call a function to start the game
    
    

    return 0
