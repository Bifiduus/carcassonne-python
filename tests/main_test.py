import io
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import carcassonne.__main__ as main_module


class MainContestModeTestCase(unittest.TestCase):
    def build_args(self, **overrides):
        defaults = {
            "version": False,
            "verbose": False,
            "debug": False,
            "shuffle": "fisher-yates",
            "seed": None,
            "gui": False,
            "file": "contest_test.txt",
            "blitz": False,
            "contest": True,
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
            patch.object(main_module, "GraphData", return_value=Mock()),
            patch.object(main_module, "GameRepository", return_value=Mock()),
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


if __name__ == "__main__":
    unittest.main()
