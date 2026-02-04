"""Main file of the program"""
import argparse
import sys

from carcassonne import __version__
from carcassonne.Presentation.Interface import GameCLI
from carcassonne.BusinessLogic.RulesEngine import RulesEngine

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
    args = parser.parse_args()
    if args.version:
        print(f"Carcassonne: version {__version__}")
    if args.debug:
        print("Debug mode enabled.", file=sys.stderr)
    elif args.verbose:
        print("Verbose mode enabled.")

    # Call a function to start the game
    game_service = RulesEngine()
    game_cli = GameCLI(game_service)
    game_cli.run()

    return 0
