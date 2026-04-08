import unittest
from configparser import ConfigParser
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from carcassonne.business_logic.game import Game
from carcassonne.datas.graph_data import GraphData
from carcassonne.datas.datas_factory import DatasFactory


class GameContestInitializationTestCase(unittest.TestCase):
    def test_game_does_not_start_new_game_in_contest_mode(self):
        with patch.object(Game, "start_new_game") as start_new_game:
            Game(
                GraphData(),
                2,
                {
                    "contest": True,
                    "contest_file": "contest_state.txt",
                },
                datas_factory=DatasFactory(),
            )

        start_new_game.assert_not_called()

    def test_stale_contest_file_in_user_config_does_not_block_normal_startup(self):
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / ".carcassonnerc"
            parser = ConfigParser()
            parser["defaults"] = {"contest_file": "contest_state.txt"}
            with config_path.open("w") as handle:
                parser.write(handle)

            with patch(
                "carcassonne.datas.game_configuration.CONFIG_PATH",
                str(config_path),
            ):
                with patch.object(Game, "start_new_game") as start_new_game:
                    Game(GraphData(), 2, datas_factory=DatasFactory())

        start_new_game.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
