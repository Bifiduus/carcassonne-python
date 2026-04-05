import unittest
from unittest.mock import patch

from carcassonne.business_logic.game import Game
from carcassonne.datas.graph_data import GraphData


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
            )

        start_new_game.assert_not_called()


if __name__ == "__main__":
    unittest.main()
