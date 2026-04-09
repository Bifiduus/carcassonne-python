"""Main file of the program"""

import argparse
from functools import partial
import signal
import sys

from carcassonne import __version__
from carcassonne.business_logic.business_logic_factory import (
    BusinessLogicFactory,
)
from carcassonne.business_logic.client import Client
from carcassonne.interfaces.i_business_logic_factory import (
    IBusinessLogicFactory,
)
from carcassonne.interfaces.i_datas_factory import IDatasFactory
from carcassonne.interfaces.i_games_repository import (
    IGamesRepository,
)
from carcassonne.business_logic.server import Server
from carcassonne.interfaces.i_client_service import IClientService
from carcassonne.interfaces.i_game_service import IGameService
from carcassonne.business_logic.game.game import Game
from carcassonne.interfaces.i_graph_data import IGraphData
from carcassonne.presentation.cli.cli import GameCLI
from carcassonne.datas.datas_factory import DatasFactory
from carcassonne.i18n import configure_i18n, gettext as _, prepare_gui_locale
from carcassonne.logger import setup_logging
from carcassonne.interfaces.i_server_service import IServerService


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str):  # pylint: disable=arguments-differ
        # Print error + help to stderr and exit with code 1.
        print(f"{_('error')}: {message}", file=sys.stderr)
        self.print_help(sys.stderr)
        raise SystemExit(1)


ALREADY_SHUTTING_DOWN: bool = False


def shutdown_all(signum, frame, server_service: IServerService,
                 client_service: IClientService):
    global ALREADY_SHUTTING_DOWN
    print(
        _(
            "Signal {signum} received: shutting down both client and server."
        ).format(signum=signum)
    )
    if ALREADY_SHUTTING_DOWN:
        print(_("Already shutting down, ignoring additional signal."))
        return
    ALREADY_SHUTTING_DOWN = True
    try:
        if client_service is not None:
            client_service.disconnect()
    except Exception as e:
        print(
            _("Error shutting down client: {error}").format(error=e),
            file=sys.stderr,
        )
    try:
        if server_service is not None:
            server_service.server_stop()
    except Exception as e:
        print(
            _("Error shutting down server: {error}").format(error=e),
            file=sys.stderr,
        )


def main() -> int:
    # pylint: disable=docstring-first-line-empty
    """
    Starting point of the program.
    """
    selected_language = configure_i18n()

    parser = ArgumentParser()
    parser.add_argument(
        "-V",
        "--version",
        help=_("display the version of the program"),
        action="store_true",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        help=_("increase verbosity"),
        action="store_true",
    )
    parser.add_argument(
        "-d",
        "--debug",
        help=_("enable debug messages"),
        action="store_true",
    )
    parser.add_argument(
        "-x",
        "--shuffle",
        metavar="SHUFFLE",
        help=_("shuffle algorithm (fisher-yates|naive)"),
        choices=["fisher-yates", "naive"],
        default="fisher-yates",
    )
    parser.add_argument(
        "-s",
        "--seed",
        help=_("seed for shuffle randomness"),
        type=int,
    )

    parser.add_argument(
        "-g",
        "--gui",
        help=_("enable GUI mode"),
        action="store_true",
    )

    parser.add_argument(
        "-f",
        "--file",
        help=_("file to load (contest mode or saved game)"),
        type=str,
    )
    parser.add_argument(
        "save_file",
        nargs="?",
        help=_("saved game file to load at startup"),
        type=str,
    )

    parser.add_argument(
        "-b",
        "--blitz",
        help=_("enable blitz mode"),
        action="store_true",
    )
    parser.add_argument(
        "-c",
        "--contest",
        help=_("enable contest mode"),
        action="store_true",
    )
    parser.add_argument(
        "-t",
        "--time",
        help=_("set time limit in minutes"),
        type=int,
        default=None,
    )

    parser.add_argument(
        "-p",
        "--players",
        help=_("number of players (default: 2)"),
        type=int,
        default=2,
    )

    parser.add_argument(
        "-r",
        "--river",
        help=_("enable river mode"),
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "-at",
        "--ai-time",
        help=_("max seconds for AI moves (default: 5s)"),
        type=int,
        default=5,
    )

    parser.add_argument(
        "-am",
        "--ai-mode",
        help=_("AI algorithm used (default from configuration: minimax)"),
        type=str,
        default="minimax",
        choices=["random", "minimax", "iterative", "mcts"],
    )

    parser.add_argument(
        "-amd",
        "--ai-minimax-depth",
        help=_(
            "depth of the AI tree search "
            "(default: maximum depth = 80 playable tiles)"
        ),
        type=int,
        default=83,
    )

    parser.add_argument(
        "--ai-minimax-scoring",
        help=_(
            "evaluation function for minimax/iterative "
            "(baseline|short_term|disruption)"
        ),
        type=str,
        choices=["baseline", "short_term", "disruption"],
        default="disruption",
    )

    parser.add_argument(
        "-ams",
        "--ai-mcts-selection",
        help=_("selection function for mcts (UCT|ML, default: UCT)"),
        type=str.upper,
        choices=["UCT", "ML"],
        default="UCT",
    )

    parser.add_argument(
        "-S",
        "--server",
        help=(
            _(
                "join a server on port [PORT] "
                "(default: don't join any server, start in local mode)"
            )
        ),
        type=str,
    )

    parser.add_argument(
        "-D",
        "--daemon",
        help=_("start the server without an interface"),
        action="store_true",
    )

    args: argparse.Namespace = parser.parse_args()
    setup_logging(verbose=args.verbose, debug=args.debug)
    if args.version:
        print(_("Carcassonne: version {version}").format(version=__version__))
        return 0

    file_to_load = args.file or args.save_file
    if args.file and args.save_file and args.file != args.save_file:
        parser.error("cannot use both FILE and --file with different values")

    if args.contest and not file_to_load:
        parser.error("--file is required when --contest is enabled")

    if args.contest and args.gui:
        parser.error(
            "--contest and --gui are mutually exclusive "
            "(contest mode is non-interactive)"
        )

    config_overrides = {}
    # CLI contract: blitz mode is enabled only when -b/--blitz is passed.
    config_overrides["blitz"] = bool(args.blitz)
    config_overrides["contest"] = bool(args.contest)
    if args.verbose:
        config_overrides["verbose"] = True
    if args.debug:
        config_overrides["debug"] = True
    if args.blitz:
        config_overrides["time"] = args.time if args.time is not None else 30
    if args.contest and file_to_load:
        config_overrides["contest_file"] = file_to_load
    # map -p/--players to num_ai_players for AI settings
    if args.players and 1 <= args.players <= 5:
        config_overrides["num_ai_players"] = args.players - 1
    if args.time is not None and not args.blitz:
        print(
            _("Warning: --time is ignored because --blitz is not enabled."),
            file=sys.stderr,
        )
    if args.ai_time:
        config_overrides["ai_time"] = args.ai_time
    if args.ai_mode is not None:
        config_overrides["ai_mode"] = args.ai_mode
    if args.ai_minimax_depth > 0:
        config_overrides["ai_minimax_depth"] = args.ai_minimax_depth
    if args.ai_minimax_scoring is not None:
        config_overrides["ai_minimax_scoring"] = args.ai_minimax_scoring
    config_overrides["ai_mcts_selection"] = args.ai_mcts_selection
    if args.river:
        print(_("River mode enabled."))
        config_overrides["river"] = True

    if args.debug:
        print(_("Debug mode enabled."), file=sys.stderr, flush=True)
    if file_to_load and not args.contest:
        print(
            _("Loading game from file: {filename}").format(
                filename=file_to_load
            ),
            flush=True,
        )
    if args.gui:
        config_overrides["gui"] = True
        print(_("GUI mode enabled."), flush=True)
    if args.verbose:
        print(_("Verbose mode enabled."), flush=True)
    if not args.gui and not args.contest:
        print(_("Welcome to Carcassonne"))
        print(_("Type 'help' to see the list of commands.") + "\n")

    business_logic_factory: IBusinessLogicFactory = BusinessLogicFactory()
    datas_factory: IDatasFactory = DatasFactory()

    game_data: IGraphData = datas_factory.create("GraphData")
    nb_players = args.players if args.players and 1 < args.players <= 5 else 2
    game: IGameService = Game(
        game_data,
        nb_players,
        config_overrides,
        shuffle_algo=args.shuffle,
        default_seed=args.seed,
        business_logic_factory=business_logic_factory,
        datas_factory=datas_factory,
    )
    game_repo: IGamesRepository = datas_factory.create("GameRepository")
    daemon: bool = bool(args.daemon)
    server_service: IServerService = Server(
        game_repo,
        daemon=daemon,
        business_logic_factory=business_logic_factory,
        datas_factory=datas_factory,
    )
    client_service: IClientService = Client(game_repo, server_service)

    # Register the global signal handler once
    handler = partial(
        shutdown_all,
        server_service=server_service,
        client_service=client_service
    )
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)

    if args.daemon:
        print(_("Starting server in daemon mode (no interface)."))
        server_service.server_start()

    if args.server:
        server_service.server_start(args.server)
        client_service.list_available_servers()
        client_service.join_server(args.server)

    # mettre en place client_service dans le reste
    game.game_data.shuffle_algo = args.shuffle
    game.game_data.default_seed = args.seed
    if args.version:
        print(_("Carcassonne: version {version}").format(version=__version__))
    if args.contest:
        try:
            move = game.game_mode_manager.run_contest()
        except ValueError as exc:
            print(
                _("Contest error: {error}").format(error=exc),
                file=sys.stderr,
            )
            return 1
        print(move)
        return 0
    if file_to_load and game.load_game_from_file(file_to_load) != 0:
        print(
            _("Failed to load the game from {filename}.").format(
                filename=file_to_load
            ),
            file=sys.stderr,
        )
        return 1
    if file_to_load:
        game.river_manager.reset()
        if game.game_data.game_configuration.get_setting_value("river"):
            game.river_manager.initialize_river()
    if args.gui:
        prepare_gui_locale(selected_language)
        from carcassonne.presentation.gui.create_gui import CreateGui

        CreateGui(game, client_service, server_service)
    else:
        game_cli = GameCLI(game, server_service, client_service)
        game_cli.run()

    # Call a function to start the game

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
