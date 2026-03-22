import unittest

from carcassonne.business_logic.game_mode_manager import GameModeManager


class DummyConfiguration:
    def __init__(self, settings):
        self.settings = settings


class DummyPlayer:
    def __init__(self, player_id: int):
        self.player_id = player_id

    def get_id(self) -> int:
        return self.player_id


class DummyGame:
    def __init__(self, settings):
        self.game_configuration = DummyConfiguration(settings)
        self.players_order = [0, 1]
        self.current_player_order_list = 0
        self.current_hand = None
        self.players = {
            0: DummyPlayer(0),
            1: DummyPlayer(1),
        }

    def get_current_player(self) -> DummyPlayer:
        player_id = self.players_order[self.current_player_order_list]
        return self.players[player_id]


class GameModeManagerTestCase(unittest.TestCase):
    def test_get_mode_returns_default_when_no_mode_is_configured(self):
        game = DummyGame({"blitz": False, "contest_file": "", "time": 30})

        manager = GameModeManager(game)

        self.assertEqual(manager.get_mode(), "default")

    def test_get_mode_returns_blitz_when_blitz_is_enabled(self):
        game = DummyGame({"blitz": True, "contest_file": "", "time": 30})

        manager = GameModeManager(game)

        self.assertEqual(manager.get_mode(), "blitz")

    def test_get_mode_prefers_contest_when_contest_file_is_set(self):
        game = DummyGame(
            {
                "blitz": True,
                "contest_file": "/tmp/contest.txt",
                "time": 30,
            }
        )

        manager = GameModeManager(game)

        self.assertEqual(manager.get_mode(), "contest")

    def test_reset_for_current_state_initializes_blitz_clock(self):
        game = DummyGame({"blitz": True, "contest_file": "", "time": 5})

        manager = GameModeManager(game)
        manager.reset_for_current_state()

        self.assertTrue(manager.blitz_manager.enabled)
        self.assertEqual(manager.blitz_manager.active_player_id, 0)
        self.assertEqual(manager.blitz_manager.get_remaining_seconds(0), 300.0)


if __name__ == "__main__":
    unittest.main()
