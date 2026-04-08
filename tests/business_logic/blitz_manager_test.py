import pytest

from carcassonne.business_logic.game.blitz_manager import BlitzManager


class DummyPlayer:
    def __init__(self, player_id: int) -> None:
        self.player_id = player_id

    def get_id(self) -> int:
        return self.player_id


class DummyGameData:
    def __init__(self, settings=None, player_ids=(0, 1)) -> None:
        self.settings = {"blitz": False, "time": 30}
        if settings:
            self.settings.update(settings)
        self.players_order = list(player_ids)
        self.current_player_order_list = 0
        self.current_hand = "CFFF"
        self.players = {
            player_id: DummyPlayer(player_id) for player_id in self.players_order
        }

    def get_game_configuration(self):
        return self.settings

    def get_current_player(self) -> DummyPlayer:
        player_id = self.players_order[self.current_player_order_list]
        return self.players[player_id]


def test_reset_normalizes_minutes_and_clears_runtime_state() -> None:
    manager = BlitzManager(DummyGameData())
    manager.active_player_id = 9
    manager.turn_started_at = 10.0
    manager.timed_out_player_ids = {9}
    manager.timeout_message = "expired"

    manager.reset([0, 1], enabled=True, minutes="invalid")

    assert manager.enabled is True
    assert manager.time_limit_seconds == 1800.0
    assert manager.remaining_time_seconds_by_player == {0: 1800.0, 1: 1800.0}
    assert manager.active_player_id is None
    assert manager.turn_started_at is None
    assert manager.get_timed_out_players() == []
    assert manager.get_timeout_message() == ""


def test_start_turn_ignores_disabled_and_timed_out_players(monkeypatch) -> None:
    manager = BlitzManager(DummyGameData())
    monkeypatch.setattr(
        "carcassonne.business_logic.game.blitz_manager.time.monotonic",
        lambda: 42.0,
    )

    manager.reset([0], enabled=False, minutes=5)
    manager.start_turn(0)
    assert manager.active_player_id is None

    manager.reset([0], enabled=True, minutes=5)
    manager.timed_out_player_ids.add(0)
    manager.start_turn(0)
    assert manager.active_player_id is None


def test_start_turn_adds_missing_player_and_uses_current_clock(monkeypatch) -> None:
    manager = BlitzManager(DummyGameData())
    manager.reset([], enabled=True, minutes=5)
    monkeypatch.setattr(
        "carcassonne.business_logic.game.blitz_manager.time.monotonic",
        lambda: 17.5,
    )

    manager.start_turn(3)

    assert manager.active_player_id == 3
    assert manager.turn_started_at == 17.5
    assert manager.get_remaining_seconds(3) == 300.0


def test_consume_now_updates_remaining_time_without_timeout(monkeypatch) -> None:
    manager = BlitzManager(DummyGameData())
    manager.reset([0], enabled=True, minutes=1)
    manager.active_player_id = 0
    manager.turn_started_at = 10.0
    manager.remaining_time_seconds_by_player[0] = 60.0
    monkeypatch.setattr(
        "carcassonne.business_logic.game.blitz_manager.time.monotonic",
        lambda: 12.5,
    )

    assert manager.consume_now() is False
    assert manager.get_remaining_seconds(0) == 57.5
    assert manager.turn_started_at == 12.5


def test_consume_now_handles_already_timed_out_and_new_timeout(monkeypatch) -> None:
    manager = BlitzManager(DummyGameData())
    manager.reset([0], enabled=True, minutes=1)
    manager.active_player_id = 0
    manager.turn_started_at = 10.0
    manager.timed_out_player_ids.add(0)

    assert manager.consume_now() is False
    assert manager.active_player_id is None
    assert manager.turn_started_at is None

    manager.reset([0], enabled=True, minutes=1)
    manager.active_player_id = 0
    manager.turn_started_at = 10.0
    manager.remaining_time_seconds_by_player[0] = 1.0
    monkeypatch.setattr(
        "carcassonne.business_logic.game.blitz_manager.time.monotonic",
        lambda: 11.5,
    )

    assert manager.consume_now() is True
    assert manager.get_remaining_seconds(0) == 0.0
    assert manager.has_timeout_loss() is True
    assert manager.get_timed_out_players() == [0]
    assert "Player 0" in manager.get_timeout_message()


def test_end_turn_starts_next_player_when_they_are_still_playable(monkeypatch) -> None:
    manager = BlitzManager(DummyGameData(settings={"blitz": True}))
    manager.reset([0, 1], enabled=True, minutes=1)
    manager.active_player_id = 0
    manager.turn_started_at = 10.0
    monkeypatch.setattr(
        "carcassonne.business_logic.game.blitz_manager.time.monotonic",
        lambda: 10.0,
    )

    assert manager.end_turn(1) is False
    assert manager.active_player_id == 1


def test_initialize_blitz_state_uses_configured_time_and_current_player() -> None:
    game_data = DummyGameData(settings={"blitz": True, "time": 5})
    game_data.current_player_order_list = 1
    manager = BlitzManager(game_data)

    manager._initialize_blitz_state()

    assert manager.enabled is True
    assert manager.time_limit_seconds == 300.0
    assert manager.active_player_id == 1


def test_skip_current_player_and_tick_blitz_advance_turns() -> None:
    game_data = DummyGameData(settings={"blitz": True, "time": 5})
    manager = BlitzManager(game_data)
    manager.reset([0, 1], enabled=True, minutes=5)

    assert manager.skip_current_player() is True
    assert game_data.current_hand is None
    assert game_data.current_player_order_list == 1
    assert manager.active_player_id == 1

    manager.tick = lambda: True
    game_data.current_hand = "CRRF"
    game_data.current_player_order_list = 0
    manager.active_player_id = None

    assert manager.tick_blitz() is True
    assert game_data.current_player_order_list == 1
    assert manager.active_player_id == 1


def test_tick_blitz_and_skip_current_player_return_false_when_no_player_exists() -> None:
    game_data = DummyGameData(settings={"blitz": True, "time": 5}, player_ids=())
    manager = BlitzManager(game_data)

    assert manager.skip_current_player() is False
    assert manager.tick_blitz() is False
    assert manager._ensure_current_player_playable() is False


def test_remaining_time_helpers_cover_enabled_and_disabled_modes() -> None:
    disabled_manager = BlitzManager(DummyGameData(settings={"blitz": False}))

    assert disabled_manager.get_current_player_remaining_time_seconds() is None
    assert disabled_manager.get_player_remaining_time_seconds(0) is None
    assert disabled_manager.get_all_players_remaining_time_seconds() == []
    assert disabled_manager._ensure_current_player_playable() is True

    enabled_game_data = DummyGameData(settings={"blitz": True, "time": 5})
    enabled_manager = BlitzManager(enabled_game_data)
    enabled_manager._initialize_blitz_state()

    assert enabled_manager._has_playable_player() is True
    assert enabled_manager.get_current_player_remaining_time_seconds() == pytest.approx(
        300.0,
        abs=0.05,
    )
    assert enabled_manager.get_player_remaining_time_seconds(42) is None
    assert enabled_manager.get_player_remaining_time_seconds(0) == pytest.approx(
        300.0,
        abs=0.05,
    )
    all_remaining = enabled_manager.get_all_players_remaining_time_seconds()

    assert all_remaining[0][0] == 0
    assert all_remaining[0][1] == pytest.approx(300.0, abs=0.05)
    assert all_remaining[1] == (1, 300.0)


def test_pause_freezes_clock_until_resume(monkeypatch) -> None:
    manager = BlitzManager(DummyGameData(settings={"blitz": True, "time": 1}))
    manager.reset([0], enabled=True, minutes=1)

    current_time = 10.0

    def fake_monotonic():
        return current_time

    monkeypatch.setattr(
        "carcassonne.business_logic.game.blitz_manager.time.monotonic",
        fake_monotonic,
    )

    manager.start_turn(0)
    current_time = 15.0
    assert manager.pause() is False
    assert manager.paused is True
    assert manager.get_remaining_seconds(0) == 55.0
    assert manager.turn_started_at is None

    current_time = 40.0
    assert manager.tick_blitz() is False
    assert manager.get_remaining_seconds(0) == 55.0

    manager.resume()
    assert manager.paused is False
    assert manager.turn_started_at == 40.0

    current_time = 42.5
    assert manager.consume_now() is False
    assert manager.get_remaining_seconds(0) == pytest.approx(52.5)
