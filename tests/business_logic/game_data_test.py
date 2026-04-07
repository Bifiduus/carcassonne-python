from carcassonne.business_logic.game.game_data import GameData
from carcassonne.business_logic.player import Player


class DummyGraph:
    def __init__(self) -> None:
        self.reset_calls = 0

    def reset_graph(self) -> None:
        self.reset_calls += 1


class DummyGameConfiguration:
    def __init__(self, overrides=None) -> None:
        self.settings = {"river": False}
        if overrides:
            self.settings.update(overrides)

    def get_setting_value(self, key):
        return self.settings.get(key)

    def get_setting(self):
        return self.settings.copy()


def test_init_adds_requested_ai_players_and_shuffles_order(monkeypatch) -> None:
    monkeypatch.setattr(
        "carcassonne.business_logic.game.game_data.GameConfiguration",
        DummyGameConfiguration,
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.game.game_data.r.shuffle",
        lambda players: players.reverse(),
    )

    data = GameData(DummyGraph(), 3)

    assert data.get_number_of_players() == 3
    assert data.get_maximum_number_of_players() == 5
    assert data.get_minimum_number_of_players() == 2
    assert data.number_of_ai_players == 2
    assert data.players_order == [2, 1, 0]
    assert data.get_current_player().get_id() == 2
    assert data.players[1].is_ai_player() is True


def test_add_online_players_replaces_existing_players_and_assigns_colors(monkeypatch) -> None:
    monkeypatch.setattr(
        "carcassonne.business_logic.game.game_data.GameConfiguration",
        DummyGameConfiguration,
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.game.game_data.r.shuffle",
        lambda players: None,
    )
    data = GameData(DummyGraph(), 2)
    online_players = [
        Player(1, "Alice", "green"),
        Player(2, "Bob", "green"),
    ]

    data.add_online_players(online_players)

    assert sorted(data.players) == [1, 2]
    assert data.players[1].get_color() == "red"
    assert data.players[2].get_color() == "blue"
    assert data.players_order == [1, 2]


def test_shuffle_players_order_is_deterministic_with_seed(monkeypatch) -> None:
    monkeypatch.setattr(
        "carcassonne.business_logic.game.game_data.GameConfiguration",
        DummyGameConfiguration,
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.game.game_data.r.shuffle",
        lambda players: None,
    )

    data_a = GameData(DummyGraph(), 3)
    data_b = GameData(DummyGraph(), 3)
    data_a.players_order = [0, 1, 2]
    data_b.players_order = [0, 1, 2]

    data_a.shuffle_players_order(123)
    data_b.shuffle_players_order(123)

    assert data_a.players_order == data_b.players_order


def test_reset_reinitializes_runtime_state_and_uses_river_start(monkeypatch) -> None:
    monkeypatch.setattr(
        "carcassonne.business_logic.game.game_data.GameConfiguration",
        DummyGameConfiguration,
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.game.game_data.r.shuffle",
        lambda players: None,
    )
    calls: list[str] = []
    monkeypatch.setattr(
        "carcassonne.business_logic.game.game_data.initialize_starting_tile",
        lambda graph: calls.append("default"),
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.game.game_data.initialize_starting_tile_river",
        lambda graph: calls.append("river"),
    )
    data = GameData(DummyGraph(), 2, {"river": True})
    old_board = data.board
    old_tiles_info = data.tiles_info
    old_history = data.history
    data.current_hand = "CFFF"
    data._end_game_scored = True

    data.reset()

    assert data.graph.reset_calls == 1
    assert calls == ["river"]
    assert data.board is not old_board
    assert data.tiles_info is not old_tiles_info
    assert data.history is not old_history
    assert data.current_hand is None
    assert data._end_game_scored is False


def test_start_load_game_rebuilds_loading_state_and_uses_default_start(monkeypatch) -> None:
    monkeypatch.setattr(
        "carcassonne.business_logic.game.game_data.GameConfiguration",
        DummyGameConfiguration,
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.game.game_data.r.shuffle",
        lambda players: None,
    )
    calls: list[str] = []
    monkeypatch.setattr(
        "carcassonne.business_logic.game.game_data.initialize_starting_tile",
        lambda graph: calls.append("default"),
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.game.game_data.initialize_starting_tile_river",
        lambda graph: calls.append("river"),
    )
    data = GameData(DummyGraph(), 2, {"river": False})
    clear_calls: list[str] = []
    data.history.clear_history = lambda: clear_calls.append("cleared")
    old_deck = data.deck
    old_repository = data.game_repository
    data.current_hand = "CRRF"
    data.current_player_order_list = 1
    data._end_game_scored = True

    data.start_load_game()

    assert clear_calls == ["cleared"]
    assert data.graph.reset_calls == 1
    assert calls == []
    assert data.deck is not old_deck
    assert data.game_repository is not old_repository
    assert data.current_hand is None
    assert data.current_player_order_list == 0
    assert data._end_game_scored is False


def test_extract_tile_code_and_is_river_over_cover_valid_and_invalid_moves(monkeypatch) -> None:
    monkeypatch.setattr(
        "carcassonne.business_logic.game.game_data.GameConfiguration",
        DummyGameConfiguration,
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.game.game_data.r.shuffle",
        lambda players: None,
    )
    data = GameData(DummyGraph(), 2)

    assert data.extract_tile_code("CFFF/0N0") == "CFFF"
    assert data.extract_tile_code("FFFF/m/0N0") == "FFFF/m"
    assert data.extract_tile_code("invalid") is None

    data.deck.river_tiles = []
    data.current_hand = None
    assert data.is_river_over() is True

    data.current_hand = "FSFS"
    assert data.is_river_over() is False
