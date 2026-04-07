from types import SimpleNamespace

from carcassonne.business_logic.game.new_game import NewGame


class DummyHistory:
    def __init__(self) -> None:
        self.clear_calls = 0

    def clear_history(self) -> None:
        self.clear_calls += 1


class DummyGraph:
    def __init__(self) -> None:
        self.reset_calls = 0

    def reset_graph(self) -> None:
        self.reset_calls += 1


class DummyPlayer:
    def __init__(self, player_id: int, is_ai: bool = False) -> None:
        self.player_id = player_id
        self.is_ai = is_ai
        self.reset_calls = 0
        self.colors = []

    def reset(self) -> None:
        self.reset_calls += 1

    def is_ai_player(self) -> bool:
        return self.is_ai

    def get_id(self) -> int:
        return self.player_id

    def set_color(self, color: str) -> None:
        self.colors.append(color)


class DummyGameConfiguration:
    def __init__(self, river: bool = False) -> None:
        self.river = river

    def get_setting_value(self, key: str):
        if key == "river":
            return self.river
        return None


class DummyRiverManager:
    def __init__(self) -> None:
        self.reset_calls = 0
        self.initialize_calls = 0

    def reset(self) -> None:
        self.reset_calls += 1

    def initialize_river(self) -> None:
        self.initialize_calls += 1


class DummyDeckManager:
    def __init__(self, resolved_seed: int = 4242) -> None:
        self.resolved_seed = resolved_seed
        self.resolve_calls = []
        self.shuffle_calls = []

    def resolve_seed(self, seed=None) -> int:
        self.resolve_calls.append(seed)
        if seed is None:
            return self.resolved_seed
        return seed

    def shuffle_deck(self, algo=None, seed=None) -> None:
        self.shuffle_calls.append((algo, seed))


class DummyBlitzManager:
    def __init__(self) -> None:
        self.init_calls = 0

    def _initialize_blitz_state(self) -> None:
        self.init_calls += 1

    def _has_playable_player(self) -> bool:
        return True


class DummyGameData:
    def __init__(self, river: bool = False) -> None:
        self.history = DummyHistory()
        self.graph = DummyGraph()
        self.game_configuration = DummyGameConfiguration(river)
        self.current_hand = "CFFF"
        self.board = "old-board"
        self.deck = "old-deck"
        self.tiles_info = "old-tiles"
        self.rules_manager = "old-rules"
        self.players = {
            0: DummyPlayer(0, is_ai=False),
            1: DummyPlayer(1, is_ai=True),
        }
        self.players_order = [0, 1]
        self.current_player_order_list = 0
        self._end_game_scored = True
        self.shuffle_calls = []
        self.shuffle_inputs = []
        self.online_players_received = None

    def get_maximum_number_of_players(self) -> int:
        return 2

    def add_online_players(self, players) -> None:
        self.online_players_received = players
        self.players = {player.get_id(): player for player in players}
        self.players_order = [player.get_id() for player in players]

    def shuffle_players_order(self, seed=None) -> None:
        self.shuffle_calls.append(seed)
        self.shuffle_inputs.append(list(self.players_order))
        self.players_order = list(reversed(self.players_order))

    def get_current_player(self):
        player_id = self.players_order[self.current_player_order_list]
        return self.players[player_id]


def install_factory_patches(monkeypatch, module_prefix: str) -> dict[str, list[str]]:
    calls = {"start": [], "river_start": [], "board": [], "deck": [], "tiles": [], "rules": []}

    class FakeBoard:
        def __init__(self) -> None:
            calls["board"].append("board")

    class FakeDeck:
        def __init__(self) -> None:
            calls["deck"].append("deck")

        def is_empty(self) -> bool:
            return False

    class FakeTilesInfo:
        def __init__(self) -> None:
            calls["tiles"].append("tiles")

    def fake_rules_manager(tiles_info):
        calls["rules"].append(tiles_info)
        return f"rules-for-{id(tiles_info)}"

    monkeypatch.setattr(
        f"{module_prefix}.initialize_starting_tile",
        lambda graph: calls["start"].append("default"),
    )
    monkeypatch.setattr(
        f"{module_prefix}.initialize_starting_tile_river",
        lambda graph: calls["river_start"].append("river"),
    )
    monkeypatch.setattr(f"{module_prefix}.Board", FakeBoard)
    monkeypatch.setattr(f"{module_prefix}.Deck", FakeDeck)
    monkeypatch.setattr(f"{module_prefix}.TilesInfo", FakeTilesInfo)
    monkeypatch.setattr(f"{module_prefix}.RulesManager", fake_rules_manager)
    return calls


def test_start_online_game_rejects_too_many_players() -> None:
    game_data = DummyGameData()
    new_game = NewGame(
        DummyRiverManager(),
        DummyDeckManager(),
        DummyBlitzManager(),
        game_data,
    )
    players = [DummyPlayer(1), DummyPlayer(2), DummyPlayer(3)]

    message = new_game.start_online_game(players)

    assert "too many players" in message
    assert game_data.history.clear_calls == 0


def test_start_online_game_resets_runtime_state_and_uses_default_start(monkeypatch) -> None:
    calls = install_factory_patches(
        monkeypatch,
        "carcassonne.business_logic.game.new_game",
    )
    game_data = DummyGameData(river=False)
    deck_manager = DummyDeckManager()
    new_game = NewGame(
        DummyRiverManager(),
        deck_manager,
        DummyBlitzManager(),
        game_data,
    )
    players = [DummyPlayer(10), DummyPlayer(20)]

    message = new_game.start_online_game(players)

    assert message == "Starting the game."
    assert game_data.history.clear_calls == 1
    assert game_data.graph.reset_calls == 1
    assert calls["start"] == ["default"]
    assert calls["river_start"] == []
    assert game_data.current_hand is None
    assert calls["board"] == ["board"]
    assert calls["deck"] == ["deck"]
    assert calls["tiles"] == ["tiles"]
    assert len(calls["rules"]) == 1
    assert game_data.online_players_received == players
    assert deck_manager.resolve_calls == [None]
    assert deck_manager.shuffle_calls == [(None, 4242)]
    assert game_data.shuffle_calls == [4242]
    assert game_data.current_player_order_list == 0


def test_start_new_game_reinitializes_state_for_river_games(monkeypatch) -> None:
    calls = install_factory_patches(
        monkeypatch,
        "carcassonne.business_logic.game.new_game",
    )
    game_data = DummyGameData(river=True)
    river_manager = DummyRiverManager()
    deck_manager = DummyDeckManager()
    blitz_manager = DummyBlitzManager()
    new_game = NewGame(
        river_manager,
        deck_manager,
        blitz_manager,
        game_data,
    )

    new_game.start_new_game(players_order=[0, 1], seed=123)

    assert game_data.history.clear_calls == 1
    assert game_data.graph.reset_calls == 1
    assert river_manager.reset_calls == 1
    assert river_manager.initialize_calls == 1
    assert calls["start"] == []
    assert calls["river_start"] == ["river"]
    assert calls["board"] == ["board"]
    assert calls["deck"] == ["deck"]
    assert calls["tiles"] == ["tiles"]
    assert len(calls["rules"]) == 1
    assert game_data.players_order == [0, 1]
    assert deck_manager.resolve_calls == [123]
    assert deck_manager.shuffle_calls == [(None, 123)]
    assert game_data.current_player_order_list == 0
    assert game_data._end_game_scored is False
    assert blitz_manager.init_calls == 1
    assert game_data.players[0].reset_calls == 1
    assert game_data.players[1].reset_calls == 1


def test_start_new_game_shuffles_players_when_order_not_provided(monkeypatch) -> None:
    install_factory_patches(
        monkeypatch,
        "carcassonne.business_logic.game.new_game",
    )
    game_data = DummyGameData(river=False)
    game_data.players[1].is_ai = False
    game_data.players_order = [1, 0]
    deck_manager = DummyDeckManager(resolved_seed=123)
    new_game = NewGame(
        DummyRiverManager(),
        deck_manager,
        DummyBlitzManager(),
        game_data,
    )

    new_game.start_new_game()

    assert deck_manager.resolve_calls == [None]
    assert deck_manager.shuffle_calls == [(None, 123)]
    assert game_data.shuffle_calls == [123]
    assert game_data.shuffle_inputs == [[0, 1]]
    assert game_data.players_order == [1, 0]


def test_start_new_game_plays_ai_turn_until_turn_moves(monkeypatch) -> None:
    install_factory_patches(
        monkeypatch,
        "carcassonne.business_logic.game.new_game",
    )
    game_data = DummyGameData(river=False)
    game_data.players = {
        0: DummyPlayer(0, is_ai=True),
        1: DummyPlayer(1, is_ai=False),
    }
    game_data.players_order = [0, 1]
    play_calls = []

    class FakeEndGame:
        def __init__(self, game_data, blitz_manager, rules_manager) -> None:
            self.calls = 0

        def end_game(self) -> bool:
            self.calls += 1
            return False

    monkeypatch.setattr(
        "carcassonne.business_logic.game.end_game.EndGame",
        FakeEndGame,
    )

    game = SimpleNamespace(
        play_ai_turn=lambda current_game: (
            play_calls.append(current_game),
            setattr(game_data, "current_player_order_list", 1),
        )
    )
    new_game = NewGame(
        DummyRiverManager(),
        DummyDeckManager(),
        DummyBlitzManager(),
        game_data,
        game=game,
    )

    new_game.start_new_game(players_order=[0, 1], seed=5)

    assert play_calls == [game]
    assert game_data.current_player_order_list == 1
