"""Main file of the program"""

import argparse
import sys

from carcassonne import __version__
from carcassonne.business_logic.client import Client
from carcassonne.business_logic.interfaces.i_games_repository\
    import IGamesRepository
from carcassonne.business_logic.server import Server
from carcassonne.datas.games_repository import GameRepository
from carcassonne.presentation.gui.create_gui import CreateGui
from carcassonne.presentation.interfaces.i_client_service import IClientService
from carcassonne.presentation.interfaces.i_game_service import IGameService
from carcassonne.business_logic.game.game import Game
from carcassonne.business_logic.interfaces.i_graph_data import IGraphData
from carcassonne.presentation.cli.cli import GameCLI
from carcassonne.datas.graph_data import GraphData
from carcassonne.presentation.interfaces.i_server_service import IServerService


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
        "-b",
        "--blitz",
        help="enable blitz mode",
        action="store_true",
    )
    parser.add_argument(
        "-c",
        "--contest",
        help="enable contest mode",
        action="store_true",
    )
    parser.add_argument(
        "-t",
        "--time",
        help="set time limit in minutes",
        type=int,
        default=None,
    )

    parser.add_argument(
        "-p",
        "--players",
        help="number of players (default: 2)",
        type=int,
        default=2,
    )

    parser.add_argument(
        "-r",
        "--river",
        help="enable river mode",
        action="store_true",
    )

    parser.add_argument(
        "-at",
        "--ai-time",
        help="max seconds for AI moves (default: 5s)",
        type=int,
        default=5,
    )

    parser.add_argument(
        "-am",
        "--ai-mode",
        help="AI algorithm we use (default: star2.5 (= minimax with pruning))",
        type=str,
        default="random",
    )

    parser.add_argument(
        "-amd",
        "--ai-minimax-depth",
        help=(
            "depth of the ai tree search "
            "(default: maximum depth = 80 playable tiles)"
        ),
        type=int,
        default=83,
    )

    parser.add_argument(
        "-ams",
        "--ai-mcts-selection",
        help="selection function for mcts (default: UCT)",
        type=str,
        default="UCT",
    )

    parser.add_argument(
        "-S",
        "--server",
        help=(
            "join a server "
            "(default: localhost:1235)"
        ),
        type=str,
    )

    parser.add_argument(
        "-D",
        "--daemon",
        help="Lance le serveur en mode sans interface.",
    )

    args: argparse.Namespace = parser.parse_args()
    if args.version:
        print(f"Carcassonne: version {__version__}")
        return 0

    if args.contest and not args.file:
        parser.error("--file is required when --contest is enabled")

    config_overrides = {}
    # CLI contract: blitz mode is enabled only when -b/--blitz is passed.
    config_overrides["blitz"] = bool(args.blitz)
    config_overrides["contest"] = bool(args.contest)
    if args.verbose:
        config_overrides["verbose"] = True
    if args.blitz:
        config_overrides["time"] = (
            args.time if args.time is not None else 30
        )
    if args.file:
        config_overrides["contest_file"] = args.file
    # map -p/--players to num_ai_players for AI settings
    if args.players and 1 <= args.players <= 5:
        config_overrides["num_ai_players"] = args.players - 1
    elif args.time is not None:
        print(
            "Warning: --time is ignored because --blitz is not enabled.",
            file=sys.stderr,
        )
    if args.ai_time:
        config_overrides["ai_time"] = args.ai_time
    if args.ai_mode == "mcts" or args.ai_mode == "random":
        config_overrides["ai_mode"] = args.ai_mode
    if args.ai_minimax_depth > 0:
        config_overrides["ai_minimax_depth"] = args.ai_minimax_depth
    if args.ai_mcts_selection == "UCT" or args.ai_mcts_selection == "ML":
        config_overrides["ai_mcts_selection"] = args.ai_mcts_selection

    game_data: IGraphData = GraphData()
    nb_players = (
        args.players if args.players and 1 < args.players <= 5 else 2
    )
    game: IGameService = Game(game_data, nb_players, config_overrides)
    game_repo: IGamesRepository = GameRepository()
    daemon: bool = bool(args.daemon)
    # Daemon dans server init ?
    server_service: IServerService = Server(game_repo)
    client_service: IClientService = Client(game_repo, server_service)
    if args.server:
        client_service.join_server(args.server)
    # mettre en place client_service dans le reste
    game.game_data.shuffle_algo = args.shuffle
    game.game_data.default_seed = args.seed
    if args.version:
        print(f"Carcassonne: version {__version__}")
    if args.debug:
        print("Debug mode enabled.", file=sys.stderr)
    if args.contest:
        try:
            move = game.game_mode_manager.run_contest()
        except ValueError as exc:
            print(f"Contest error: {exc}", file=sys.stderr)
            return 1
        print(move)
    if args.file:
        print(f"Loading game from file: {args.file}")
    if args.verbose:
        print("Verbose mode enabled.")
    if args.river:
        print("River mode enabled.")
        game.game_data.river_manager.initialize_river()
    if args.gui:
        print("GUI mode enabled.")
        CreateGui(game)
    else:
        game_cli = GameCLI(game, server_service, client_service)
        game_cli.run()

    # Call a function to start the game

    return 0
