import unittest
from unittest.mock import patch

from carcassonne.business_logic.game_mode_manager import GameModeManager


class DummyBlitzManager:
    def __init__(self):
        self.enabled = False
        self.active_player_id = None
        self.remaining_time_seconds_by_player = {}
        self.timed_out_player_ids = set()

    def reset(self, player_ids, enabled, minutes=30):
        self.enabled = enabled
        time_limit_seconds = float(minutes * 60)
        self.remaining_time_seconds_by_player = {
            player_id: time_limit_seconds for player_id in player_ids
        }
        self.active_player_id = None

    def is_player_timed_out(self, player_id):
        return player_id in self.timed_out_player_ids

    def start_turn(self, player_id):
        self.active_player_id = player_id

    def get_remaining_seconds(self, player_id):
        return self.remaining_time_seconds_by_player[player_id]

    def tick(self):
        return False

    def get_timeout_message(self):
        return ""


class DummyPlayer:
    def __init__(self, player_id: int):
        self.player_id = player_id

    def get_id(self) -> int:
        return self.player_id


class DummyGame:
    def __init__(self, settings):
        self.settings = settings
        players = {
            0: DummyPlayer(0),
            1: DummyPlayer(1),
        }
        self.game_data = type(
            "GameData",
            (),
            {
                "players_order": [0, 1],
                "current_player_order_list": 0,
                "current_hand": None,
                "players": players,
            },
        )()

    def get_game_configuration(self):
        return self.settings

    def get_players_order(self):
        return self.game_data.players_order

    def get_current_player(self) -> DummyPlayer:
        player_id = self.game_data.players_order[
            self.game_data.current_player_order_list
        ]
        return self.game_data.players[player_id]


class GameModeManagerTestCase(unittest.TestCase):
    def create_manager(self, settings):
        game = DummyGame(settings)
        blitz_manager = DummyBlitzManager()
        return GameModeManager(blitz_manager, game), blitz_manager

    def test_get_mode_returns_default_when_no_mode_is_configured(self):
        manager, _ = self.create_manager(
            {"blitz": False, "contest_file": "", "time": 30}
        )

        self.assertEqual(manager.get_mode(), "default")

    def test_get_mode_returns_blitz_when_blitz_is_enabled(self):
        manager, _ = self.create_manager(
            {"blitz": True, "contest_file": "", "time": 30}
        )

        self.assertEqual(manager.get_mode(), "blitz")

    def test_get_mode_returns_contest_when_contest_is_enabled(self):
        manager, _ = self.create_manager(
            {
                "blitz": False,
                "contest": True,
                "contest_file": "/tmp/contest.txt",
                "time": 30,
            }
        )

        self.assertEqual(manager.get_mode(), "contest")

    def test_get_mode_prefers_contest_when_contest_file_is_set(self):
        manager, _ = self.create_manager(
            {
                "blitz": True,
                "contest_file": "/tmp/contest.txt",
                "time": 30,
            }
        )

        self.assertEqual(manager.get_mode(), "contest")

    def test_run_contest_uses_configured_filename(self):
        manager, _ = self.create_manager({"contest_file": "/tmp/contest.txt"})

        with patch.object(
            manager.contest_manager, "run", return_value="CFFF/0N0"
        ) as run_mock:
            move = manager.run_contest()

        self.assertEqual(move, "CFFF/0N0")
        run_mock.assert_called_once_with("/tmp/contest.txt")

    def test_reset_for_current_state_initializes_blitz_clock(self):
        manager, blitz_manager = self.create_manager(
            {"blitz": True, "contest_file": "", "time": 5}
        )

        manager.reset_for_current_state()

        self.assertTrue(blitz_manager.enabled)
        self.assertEqual(blitz_manager.active_player_id, 0)
        self.assertEqual(blitz_manager.get_remaining_seconds(0), 300.0)


if __name__ == "__main__":
    unittest.main()
