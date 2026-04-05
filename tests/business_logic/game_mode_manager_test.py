import unittest
from unittest.mock import patch

from carcassonne.business_logic.game_mode_manager import GameModeManager


class DummyBlitzManager:
    def __init__(self):
        self.enabled = False
        self.active_player_id = None
        self.remaining_time_seconds_by_player = {}
        self.timed_out_player_ids = set()
        self.start_turn_calls = []
        self.tick_result = False
        self.timeout_message = "timed out"

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
        self.start_turn_calls.append(player_id)

    def get_remaining_seconds(self, player_id):
        return self.remaining_time_seconds_by_player[player_id]

    def tick(self):
        return self.tick_result

    def get_timeout_message(self):
        return self.timeout_message


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


class EmptyPlayersGame(DummyGame):
    def __init__(self, settings):
        super().__init__(settings)
        self.game_data.players_order = []


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

    def test_get_configured_blitz_minutes_falls_back_to_default(self):
        manager, _ = self.create_manager({"blitz": True, "time": "invalid"})

        self.assertEqual(manager.get_configured_blitz_minutes(), 30)

    def test_get_configured_blitz_minutes_rejects_non_positive_values(self):
        manager, _ = self.create_manager({"blitz": True, "time": 0})

        self.assertEqual(manager.get_configured_blitz_minutes(), 30)

    def test_has_playable_player_handles_empty_and_default_modes(self):
        empty_game = EmptyPlayersGame({"blitz": True, "time": 5})
        manager = GameModeManager(DummyBlitzManager(), empty_game)
        self.assertFalse(manager.has_playable_player())

        manager, _ = self.create_manager({"blitz": False, "time": 5})
        self.assertTrue(manager.has_playable_player())

    def test_has_playable_player_returns_false_when_all_players_are_timed_out(self):
        manager, blitz_manager = self.create_manager({"blitz": True, "time": 5})
        blitz_manager.timed_out_player_ids = {0, 1}

        self.assertFalse(manager.has_playable_player())

    def test_advance_to_next_playable_player_skips_timed_out_players(self):
        manager, blitz_manager = self.create_manager({"blitz": True, "time": 5})
        blitz_manager.timed_out_player_ids = {0}

        result = manager.advance_to_next_playable_player()

        self.assertTrue(result)
        self.assertEqual(manager.game.game_data.current_player_order_list, 1)

    def test_advance_to_next_playable_player_handles_empty_default_and_all_timed_out(self):
        empty_game = EmptyPlayersGame({"blitz": True, "time": 5})
        manager = GameModeManager(DummyBlitzManager(), empty_game)
        self.assertFalse(manager.advance_to_next_playable_player())

        manager, blitz_manager = self.create_manager({"blitz": False, "time": 5})
        self.assertTrue(manager.advance_to_next_playable_player())

        manager, blitz_manager = self.create_manager({"blitz": True, "time": 5})
        blitz_manager.timed_out_player_ids = {0, 1}
        self.assertFalse(manager.advance_to_next_playable_player())

    def test_skip_current_player_handles_empty_players_and_default_mode(self):
        empty_game = EmptyPlayersGame({"blitz": True, "time": 5})
        manager = GameModeManager(DummyBlitzManager(), empty_game)
        self.assertFalse(manager.skip_current_player())

        manager, blitz_manager = self.create_manager({"blitz": False, "time": 5})
        manager.game.game_data.current_hand = "CFFF"
        self.assertTrue(manager.skip_current_player())
        self.assertEqual(blitz_manager.start_turn_calls, [])

    def test_skip_current_player_returns_false_when_no_player_can_continue(self):
        manager, blitz_manager = self.create_manager({"blitz": True, "time": 5})
        blitz_manager.timed_out_player_ids = {0, 1}

        self.assertFalse(manager.skip_current_player())

    def test_skip_current_player_clears_hand_and_starts_next_playable_player(self):
        manager, blitz_manager = self.create_manager({"blitz": True, "time": 5})
        manager.game.game_data.current_hand = "CFFF"

        result = manager.skip_current_player()

        self.assertTrue(result)
        self.assertIsNone(manager.game.game_data.current_hand)
        self.assertEqual(manager.game.game_data.current_player_order_list, 1)
        self.assertEqual(blitz_manager.active_player_id, 1)

    def test_ensure_current_player_playable_starts_timer_for_next_available_player(self):
        manager, blitz_manager = self.create_manager({"blitz": True, "time": 5})
        blitz_manager.timed_out_player_ids = {0}

        result = manager.ensure_current_player_playable()

        self.assertTrue(result)
        self.assertEqual(manager.game.game_data.current_player_order_list, 1)
        self.assertEqual(blitz_manager.active_player_id, 1)

    def test_ensure_current_player_playable_handles_non_blitz_and_unavailable_players(self):
        manager, _ = self.create_manager({"blitz": False, "time": 5})
        self.assertTrue(manager.ensure_current_player_playable())

        manager, blitz_manager = self.create_manager({"blitz": True, "time": 5})
        blitz_manager.timed_out_player_ids = {0, 1}
        self.assertFalse(manager.ensure_current_player_playable())

        manager, blitz_manager = self.create_manager({"blitz": True, "time": 5})
        manager.reset_for_current_state()
        blitz_manager.start_turn_calls.clear()
        self.assertTrue(manager.ensure_current_player_playable())
        self.assertEqual(blitz_manager.start_turn_calls, [])

    def test_tick_skips_to_next_player_when_current_one_times_out(self):
        manager, blitz_manager = self.create_manager({"blitz": True, "time": 5})
        blitz_manager.tick_result = True

        result = manager.tick()

        self.assertTrue(result)
        self.assertEqual(manager.game.game_data.current_player_order_list, 1)
        self.assertEqual(blitz_manager.active_player_id, 1)

    def test_tick_handles_non_blitz_no_playable_player_and_no_timeout(self):
        manager, _ = self.create_manager({"blitz": False, "time": 5})
        self.assertFalse(manager.tick())

        manager, blitz_manager = self.create_manager({"blitz": True, "time": 5})
        blitz_manager.timed_out_player_ids = {0, 1}
        self.assertFalse(manager.tick())

        manager, blitz_manager = self.create_manager({"blitz": True, "time": 5})
        manager.reset_for_current_state()
        blitz_manager.start_turn_calls.clear()
        self.assertFalse(manager.tick())
        self.assertEqual(blitz_manager.start_turn_calls, [])

    def test_current_player_time_helper_returns_blitz_value(self):
        manager, _ = self.create_manager({"blitz": True, "time": 5})
        manager.reset_for_current_state()

        self.assertEqual(
            manager.get_current_player_remaining_time_seconds(),
            300.0,
        )

    def test_time_helpers_return_none_or_empty_when_blitz_is_disabled(self):
        manager, _ = self.create_manager({"blitz": False, "time": 5})

        self.assertIsNone(manager.get_current_player_remaining_time_seconds())
        self.assertIsNone(manager.get_player_remaining_time_seconds(0))
        self.assertEqual(manager.get_all_players_remaining_time_seconds(), [])

    def test_time_helpers_handle_unknown_player_and_timeout_message(self):
        manager, blitz_manager = self.create_manager({"blitz": True, "time": 5})
        manager.reset_for_current_state()

        self.assertEqual(manager.get_timeout_message(), "timed out")
        self.assertIsNone(manager.get_player_remaining_time_seconds(42))
        self.assertEqual(
            manager.get_all_players_remaining_time_seconds(),
            [(0, 300.0), (1, 300.0)],
        )


if __name__ == "__main__":
    unittest.main()
