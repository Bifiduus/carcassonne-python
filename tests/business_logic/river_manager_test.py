from types import SimpleNamespace

from carcassonne.business_logic.game.river_manager import RiverManager


def create_manager() -> RiverManager:
    game_data = SimpleNamespace(
        tiles_info=SimpleNamespace(direction_dict={"N": 0, "E": 1, "S": 2, "W": 3})
    )
    return RiverManager(game_data)


def test_river_manager_initialization_and_reset() -> None:
    manager = create_manager()

    assert manager.is_river_active() is False
    assert manager.river_previous_opposite_direction == 0
    assert manager.river_turn is None

    manager.initialize_river()

    assert manager.is_river_active() is True
    assert manager.river_previous_opposite_direction == 0
    assert manager.river_turn is None

    manager.river_turn = 2
    manager.reset()

    assert manager.is_river_active() is False
    assert manager.river_previous_opposite_direction == 0
    assert manager.river_turn is None


def test_river_takes_turn_tracks_previous_opposite_direction() -> None:
    manager = create_manager()

    manager.river_takes_turn(1)
    assert manager.river_turn == 1
    assert manager.river_previous_opposite_direction == 0

    manager.river_takes_turn(3)

    assert manager.river_turn == 3
    assert manager.river_previous_opposite_direction == 3


def test_check_river_turn_rejects_immediate_reverse_direction() -> None:
    manager = create_manager()
    manager.river_turn = 3
    manager.river_previous_opposite_direction = 1

    assert manager.check_river_turn(["FSFS", "0N0"]) is False
    assert manager.check_river_turn(["FSRS", "m", "0N0"]) is False


def test_check_river_turn_accepts_valid_bend_and_update_tracks_it() -> None:
    manager = create_manager()

    assert manager.check_river_turn(["FFSF", "0E0"]) is True

    manager.update_river_turn(["FFSF", "0E0"])

    assert manager.river_turn == 2
    assert manager.river_previous_opposite_direction == 0


def test_update_river_turn_ignores_reverse_direction_and_straight_river() -> None:
    manager = create_manager()
    manager.river_turn = 0
    manager.river_previous_opposite_direction = 2

    manager.update_river_turn(["FFSF", "0E0"])
    assert manager.river_turn == 0

    manager.river_turn = 1
    manager.river_previous_opposite_direction = 3
    manager.update_river_turn(["FSFS", "0N0"])
    assert manager.river_turn == 1
