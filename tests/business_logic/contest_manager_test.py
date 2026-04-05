import unittest
from unittest.mock import patch

from carcassonne.business_logic.contest_manager import ContestManager


class DummyPlayer:
    def __init__(self, player_id: int):
        self.player_id = player_id

    def get_id(self) -> int:
        return self.player_id


class DummyGame:
    def __init__(self):
        self.current_hand = "CFFF"
        self.loaded_filename = None
        self.played = False
        self.settings = {
            "ai_mode": "random",
            "ai_time": 5,
            "ai_minimax_depth": 2,
            "ai_mcts_selection": "UCT",
        }
        self.history = type("History", (), {"past_moves": []})()
        self.game_data = type("GameData", (), {"history": self.history})()
        self.player = DummyPlayer(0)
        self.player.is_ai = False

    def load_game_from_file(self, filename: str) -> int:
        self.loaded_filename = filename
        return 0

    def get_game_configuration(self) -> dict:
        return self.settings

    def get_current_player(self) -> DummyPlayer:
        return self.player

    def draw_tile(self) -> str | None:
        return self.current_hand

    def play_ai_turn(self, game=None) -> None:
        self.played = True
        record = type("Record", (), {"move_str": "CFFF/0N0"})()
        self.history.past_moves.append(record)


class ContestManagerTestCase(unittest.TestCase):
    def test_run_requires_filename(self):
        manager = ContestManager(DummyGame())

        with self.assertRaises(ValueError):
            manager.run("")

    def test_run_returns_move_from_random_ai(self):
        game = DummyGame()
        manager = ContestManager(game)

        with patch.object(manager, "_load_position", return_value=None):
            move = manager.run("contest_state.txt")

        self.assertEqual(move, "CFFF/0N0")
        self.assertTrue(game.played)
        self.assertFalse(game.player.is_ai)

    def test_run_fails_when_loader_returns_error(self):
        manager = ContestManager(DummyGame())

        with (
            patch.object(
                manager,
                "_load_position",
                side_effect=ValueError("load failure"),
            ),
            self.assertRaises(ValueError),
        ):
            manager.run("contest_state.txt")


if __name__ == "__main__":
    unittest.main()
