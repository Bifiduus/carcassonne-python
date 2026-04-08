import io
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import carcassonne.__main__ as main_module


def build_args(**overrides):
    defaults = {
        "version": False,
        "verbose": False,
        "debug": False,
        "shuffle": "fisher-yates",
        "seed": None,
        "gui": False,
        "file": None,
        "blitz": False,
        "contest": False,
        "time": None,
        "players": 2,
        "river": False,
        "ai_time": 5,
        "ai_mode": "random",
        "ai_minimax_depth": 83,
        "ai_minimax_scoring": None,
        "ai_mcts_selection": "UCT",
        "server": None,
        "daemon": False,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class MainContestModeTestCase(unittest.TestCase):
    def build_args(self, **overrides):
        return build_args(file="contest_test.txt", contest=True, **overrides)

    def test_main_returns_after_contest_and_skips_cli(self):
        game = Mock()
        game.game_mode_manager.run_contest.return_value = "CFFF/0N0"
        game.game_data = Mock()

        with (
            patch.object(main_module, "configure_i18n"),
            patch.object(main_module.signal, "signal"),
            patch.object(
                main_module.ArgumentParser,
                "parse_args",
                return_value=self.build_args(),
            ),
            patch.object(main_module, "Server", return_value=Mock()),
            patch.object(main_module, "Client", return_value=Mock()),
            patch.object(main_module, "Game", return_value=game),
            patch.object(main_module, "GameCLI") as game_cli_class,
            patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            exit_code = main_module.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout.getvalue(), "CFFF/0N0\n")
        game.game_mode_manager.run_contest.assert_called_once_with()
        game_cli_class.assert_not_called()


class MainBootstrapTestCase(unittest.TestCase):
    def test_argument_parser_error_prints_help_and_exits(self):
        parser = main_module.ArgumentParser()
        stderr = io.StringIO()

        with (
            patch("sys.stderr", stderr),
            patch.object(parser, "print_help") as print_help,
            self.assertRaises(SystemExit) as exc,
        ):
            parser.error("bad flag")

        self.assertEqual(exc.exception.code, 1)
        self.assertIn("error: bad flag", stderr.getvalue())
        print_help.assert_called_once_with(stderr)

    def test_main_version_returns_early(self):
        with (
            patch.object(main_module, "configure_i18n"),
            patch.object(
                main_module.ArgumentParser,
                "parse_args",
                return_value=build_args(version=True),
            ),
            patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            exit_code = main_module.main()

        self.assertEqual(exit_code, 0)
        self.assertIn("Carcassonne: version", stdout.getvalue())

    def test_main_requires_file_when_contest_is_enabled(self):
        with (
            patch.object(main_module, "configure_i18n"),
            patch.object(
                main_module.ArgumentParser,
                "parse_args",
                return_value=build_args(contest=True, file=None),
            ),
            patch("sys.stderr", new_callable=io.StringIO) as stderr,
            self.assertRaises(SystemExit) as exc,
        ):
            main_module.main()

        self.assertEqual(exc.exception.code, 1)
        self.assertIn("--file is required", stderr.getvalue())

    def test_main_contest_error_returns_one(self):
        game = Mock()
        game.game_mode_manager.run_contest.side_effect = ValueError("boom")
        game.game_data = Mock()

        with (
            patch.object(main_module, "configure_i18n"),
            patch.object(main_module.signal, "signal"),
            patch.object(
                main_module.ArgumentParser,
                "parse_args",
                return_value=build_args(contest=True, file="contest.txt"),
            ),
            patch.object(main_module, "Server", return_value=Mock()),
            patch.object(main_module, "Client", return_value=Mock()),
            patch.object(main_module, "Game", return_value=game),
            patch("sys.stderr", new_callable=io.StringIO) as stderr,
        ):
            exit_code = main_module.main()

        self.assertEqual(exit_code, 1)
        self.assertIn("Contest error: boom", stderr.getvalue())

    def test_main_bootstraps_daemon_server_and_cli_mode(self):
        game = Mock()
        game.game_data = Mock()
        server = Mock()
        client = Mock()
        game_cli = Mock()

        with (
            patch.object(main_module, "configure_i18n"),
            patch.object(main_module.signal, "signal"),
            patch.object(
                main_module.ArgumentParser,
                "parse_args",
                return_value=build_args(
                    verbose=True,
                    debug=True,
                    shuffle="naive",
                    seed=123,
                    file="save.txt",
                    river=True,
                    time=15,
                    players=0,
                    server="4242",
                    daemon=True,
                ),
            ),
            patch.object(main_module, "Server", return_value=server),
            patch.object(main_module, "Client", return_value=client),
            patch.object(main_module, "Game", return_value=game) as game_class,
            patch.object(main_module, "GameCLI", return_value=game_cli),
            patch("sys.stdout", new_callable=io.StringIO) as stdout,
            patch("sys.stderr", new_callable=io.StringIO) as stderr,
        ):
            exit_code = main_module.main()

        self.assertEqual(exit_code, 0)
        server.server_start.assert_any_call()
        server.server_start.assert_any_call("4242")
        client.list_available_servers.assert_called_once_with()
        client.join_server.assert_called_once_with("4242")
        game_cli.run.assert_called_once_with()
        self.assertEqual(game_class.call_args.kwargs["shuffle_algo"], "naive")
        self.assertEqual(game_class.call_args.kwargs["default_seed"], 123)
        self.assertEqual(game.game_data.shuffle_algo, "naive")
        self.assertEqual(game.game_data.default_seed, 123)
        self.assertIn("River mode enabled.", stdout.getvalue())
        self.assertIn("Loading game from file: save.txt", stdout.getvalue())
        self.assertIn("Verbose mode enabled.", stdout.getvalue())
        self.assertIn("Starting server in daemon mode", stdout.getvalue())
        self.assertIn("Warning: --time is ignored", stderr.getvalue())
        self.assertIn("Debug mode enabled.", stderr.getvalue())

    def test_main_gui_mode_uses_create_gui(self):
        game = Mock()
        game.game_data = Mock()
        create_gui = Mock()
        fake_gui_module = SimpleNamespace(CreateGui=create_gui)

        with (
            patch.object(main_module, "configure_i18n"),
            patch.object(main_module.signal, "signal"),
            patch.object(
                main_module.ArgumentParser,
                "parse_args",
                return_value=build_args(gui=True),
            ),
            patch.object(main_module, "Server", return_value=Mock()),
            patch.object(main_module, "Client", return_value=Mock()),
            patch.object(main_module, "Game", return_value=game),
            patch.object(main_module, "GameCLI") as game_cli_class,
            patch.dict(
                sys.modules,
                {"carcassonne.presentation.gui.create_gui": fake_gui_module},
            ),
            patch("sys.stdout", new_callable=io.StringIO) as stdout,
        ):
            exit_code = main_module.main()

        self.assertEqual(exit_code, 0)
        create_gui.assert_called_once()
        game_cli_class.assert_not_called()
        self.assertIn("GUI mode enabled.", stdout.getvalue())

    def test_shutdown_all_disconnects_once_and_handles_errors(self):
        main_module.ALREADY_SHUTTING_DOWN = False
        client = Mock()
        server = Mock()

        with patch("sys.stdout", new_callable=io.StringIO) as stdout:
            main_module.shutdown_all(15, None, server, client)
            main_module.shutdown_all(15, None, server, client)

        client.disconnect.assert_called_once_with()
        self.assertIn("Already shutting down", stdout.getvalue())

        main_module.ALREADY_SHUTTING_DOWN = False
        failing_client = Mock()
        failing_client.disconnect.side_effect = RuntimeError("oops")

        with (
            patch("sys.stdout", new_callable=io.StringIO),
            patch("sys.stderr", new_callable=io.StringIO) as stderr,
        ):
            main_module.shutdown_all(2, None, server, failing_client)

        self.assertIn("Error shutting down client: oops", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
