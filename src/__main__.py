"""Main file of the program"""
import argparse

from src import __version__
from Presentation.Interface import GameCLI
from BusinessLogic.RulesEngine import RulesEngine

def main():
    # pylint: disable=docstring-first-line-empty
    """
    Starting point of the program.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-V",
        "--version",
        help="display the version of the program",
        action="store_true",
    )
    args = parser.parse_args()
    if args.version:
        print(f"Carcassonne: version {__version__}")

    # Call a function to start the game
    game_service = RulesEngine()
    game_cli = GameCLI(game_service)
    game_cli.run()

    return 0
