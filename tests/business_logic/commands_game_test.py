from carcassonne.business_logic.game.commands_game import CommandsGame


class DummyBlitzManager:
    def __init__(self, timed_out: bool = False, playable: bool = True) -> None:
        self.timed_out = timed_out
        self.playable = playable
        self.tick_calls = 0

    def tick_blitz(self) -> bool:
        self.tick_calls += 1
        return self.timed_out

    def _ensure_current_player_playable(self) -> bool:
        return self.playable


class DummyDeckManager:
    def __init__(self, game_data, next_hand) -> None:
        self.game_data = game_data
        self.next_hand = next_hand
        self.draw_calls = 0

    def draw_tile(self) -> None:
        self.draw_calls += 1
        self.game_data.current_hand = self.next_hand


class DummyPlayer:
    def __init__(self, player_id: int = 0, username: str = "AI") -> None:
        self.player_id = player_id
        self.username = username

    def get_username(self) -> str:
        return self.username

    def get_id(self) -> int:
        return self.player_id


class DummyGameData:
    def __init__(self, configuration: dict, player=None) -> None:
        self.configuration = configuration
        self.player = player or DummyPlayer()
        self.current_hand = None
        self.shuffled = False

    def get_current_player(self):
        return self.player

    def get_game_configuration(self):
        return dict(self.configuration)

    def shuffle_players_order(self) -> None:
        self.shuffled = True


def test_provide_hint_returns_empty_on_timeout_or_unplayable_player() -> None:
    data = DummyGameData({"ai_mode": "random"})
    command = CommandsGame(
        DummyBlitzManager(timed_out=True),
        DummyDeckManager(data, "CFFF"),
        data,
        game=object(),
    )
    assert command.provide_hint() == ""

    blocked = CommandsGame(
        DummyBlitzManager(playable=False),
        DummyDeckManager(data, "CFFF"),
        data,
        game=object(),
    )
    assert blocked.provide_hint() == ""


def test_provide_hint_returns_empty_when_no_tile_is_drawn() -> None:
    data = DummyGameData({"ai_mode": "random"})
    deck_manager = DummyDeckManager(data, None)
    command = CommandsGame(
        DummyBlitzManager(),
        deck_manager,
        data,
        game=object(),
    )

    assert command.provide_hint() == ""
    assert deck_manager.draw_calls == 1


def test_provide_hint_random_mode_uses_random_player(monkeypatch) -> None:
    created = {}

    class FakeRandomPlayer:
        def random_move(self, hand, game):
            created["args"] = (hand, game)
            return "CFFF/0N0"

    monkeypatch.setattr(
        "carcassonne.business_logic.ai_model.RandomPlayer",
        FakeRandomPlayer,
    )
    data = DummyGameData({"ai_mode": "random"})
    game = object()
    command = CommandsGame(
        DummyBlitzManager(),
        DummyDeckManager(data, "CFFF"),
        data,
        game=game,
    )

    move = command.provide_hint()

    assert move == "CFFF/0N0"
    assert created["args"] == ("CFFF", game)


def test_provide_hint_expectimax_requires_game_and_passes_search_parameters(
    monkeypatch,
) -> None:
    data = DummyGameData(
        {
            "ai_mode": "expectimax",
            "ai_time": 7.5,
            "ai_minimax_depth": 3,
            "ai_minimax_scoring": "short",
        }
    )
    command = CommandsGame(
        DummyBlitzManager(),
        DummyDeckManager(data, "CFFF"),
        data,
        game=None,
    )
    assert command.provide_hint() == ""

    created = {}

    class FakeExpectimaxPlayer:
        def __init__(self, game, start_time, ai_time, depth, eval_name) -> None:
            created["init"] = (game, start_time, ai_time, depth, eval_name)
            self.depth_max = depth

        def search(self, game, **kwargs):
            created["search"] = (game, kwargs)
            return 12.0, "FFFF/m/0N0"

    monkeypatch.setattr(
        "carcassonne.business_logic.ai_model.ExpectimaxPlayer",
        FakeExpectimaxPlayer,
    )
    monkeypatch.setattr("time.time", lambda: 42.0)
    game = object()
    command = CommandsGame(
        DummyBlitzManager(),
        DummyDeckManager(data, "FFFF/m"),
        data,
        game=game,
    )

    move = command.provide_hint()

    assert move == "FFFF/m/0N0"
    assert created["init"] == (game, 42.0, 7.5, 3, "short")
    assert created["search"][0] is game
    assert created["search"][1]["depth"] == 3
    assert created["search"][1]["player_to_max"] == 0
    assert created["search"][1]["next_player"] == 0


def test_provide_hint_iterative_mode_uses_iterative_player(monkeypatch) -> None:
    created = {}

    class FakeIterativePlayer:
        def __init__(self, game, start_time, ai_time, depth, eval_name) -> None:
            created["init"] = (game, start_time, ai_time, depth, eval_name)

        def search(self, game, **kwargs):
            created["search"] = (game, kwargs)
            return 5.0, "CFFF/0N0/N"

    monkeypatch.setattr(
        "carcassonne.business_logic.ai_model.IterativeDeepeningPlayer",
        FakeIterativePlayer,
    )
    monkeypatch.setattr("time.time", lambda: 21.0)
    data = DummyGameData(
        {
            "ai_mode": "iterative",
            "ai_time": 4.0,
            "ai_minimax_depth": 2,
            "ai_minimax_scoring": "baseline",
        }
    )
    game = object()
    command = CommandsGame(
        DummyBlitzManager(),
        DummyDeckManager(data, "CFFF"),
        data,
        game=game,
    )

    move = command.provide_hint()

    assert move == "CFFF/0N0/N"
    assert created["init"] == (game, 21.0, 4.0, 2, "baseline")
    assert created["search"][0] is game
    assert created["search"][1]["player_to_max"] == 0


def test_shuffle_players_order_delegates_to_game_data() -> None:
    data = DummyGameData({"ai_mode": "random"})
    command = CommandsGame(
        DummyBlitzManager(),
        DummyDeckManager(data, "CFFF"),
        data,
        game=None,
    )

    command.shuffle_players_order()

    assert data.shuffled is True
