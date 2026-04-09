from types import SimpleNamespace

from carcassonne.business_logic.game.end_game import EndGame


class DummyDeck:
    def __init__(self, empty: bool) -> None:
        self.empty = empty

    def is_empty(self) -> bool:
        return self.empty


class DummyBlitzManager:
    def __init__(self, has_playable_player: bool) -> None:
        self.has_playable_player = has_playable_player

    def _has_playable_player(self) -> bool:
        return self.has_playable_player


class DummyScoreManager:
    def __init__(self) -> None:
        self.calls: list[tuple[object, object]] = []

    def score_end_of_game(self, graph, players) -> None:
        self.calls.append((graph, players))


class DummyPlayer:
    def __init__(self, username: str, score: int) -> None:
        self.username = username
        self.score = score

    def get_username(self) -> str:
        return self.username

    def get_score_int(self) -> int:
        return self.score


def create_game_data(empty: bool, playable: bool, already_scored: bool = False):
    return SimpleNamespace(
        _end_game_scored=already_scored,
        deck=DummyDeck(empty),
        graph=object(),
        players={"p0": object()},
    ), DummyBlitzManager(playable)


class DummyPlayerScoreObject:
    def __init__(self, score: int) -> None:
        self.score = score


class DummyPlayerWithGetScore:
    def __init__(self, value) -> None:
        self._value = value

    def get_score(self):
        return self._value


class DummyPlayerWithScoreAttr:
    def __init__(self, value) -> None:
        self.score = value


def test_end_game_returns_true_without_scoring_twice() -> None:
    game_data, blitz_manager = create_game_data(
        empty=False,
        playable=True,
        already_scored=True,
    )
    score_manager = DummyScoreManager()
    end_game = EndGame(game_data, blitz_manager, score_manager)

    assert end_game.end_game() is True
    assert score_manager.calls == []


def test_end_game_scores_when_deck_is_empty() -> None:
    game_data, blitz_manager = create_game_data(
        empty=True,
        playable=True,
    )
    score_manager = DummyScoreManager()
    end_game = EndGame(game_data, blitz_manager, score_manager)

    assert end_game.end_game() is True
    assert score_manager.calls == [(game_data.graph, game_data.players)]
    assert game_data._end_game_scored is True


def test_end_game_scores_when_no_player_can_still_play() -> None:
    game_data, blitz_manager = create_game_data(
        empty=False,
        playable=False,
    )
    score_manager = DummyScoreManager()
    end_game = EndGame(game_data, blitz_manager, score_manager)

    assert end_game.end_game() is True
    assert score_manager.calls == [(game_data.graph, game_data.players)]


def test_end_game_returns_false_while_game_can_continue() -> None:
    game_data, blitz_manager = create_game_data(
        empty=False,
        playable=True,
    )
    score_manager = DummyScoreManager()
    end_game = EndGame(game_data, blitz_manager, score_manager)

    assert end_game.end_game() is False
    assert score_manager.calls == []
    assert game_data._end_game_scored is False


def test_end_game_scores_when_no_playable_tiles_flag_is_set() -> None:
    game_data, blitz_manager = create_game_data(empty=False, playable=True)
    game_data.no_playable_tiles_remaining = True
    score_manager = DummyScoreManager()
    end_game = EndGame(game_data, blitz_manager, score_manager)

    assert end_game.end_game() is True
    assert score_manager.calls == [(game_data.graph, game_data.players)]
    assert game_data._end_game_scored is True
    assert game_data.no_playable_tiles_remaining is False


def test_end_game_get_winner_returns_single_high_score_player() -> None:
    game_data, blitz_manager = create_game_data(empty=False, playable=True)
    game_data.players = {
        0: DummyPlayer("Alice", 12),
        1: DummyPlayer("Bob", 8),
    }
    end_game = EndGame(game_data, blitz_manager, DummyScoreManager())

    winner = end_game.get_winner()

    assert winner is not None
    assert winner.get_username() == "Alice"
    assert end_game.is_draw() is False


def test_end_game_get_winner_returns_none_on_draw() -> None:
    game_data, blitz_manager = create_game_data(empty=False, playable=True)
    game_data.players = {
        0: DummyPlayer("Alice", 12),
        1: DummyPlayer("Bob", 12),
    }
    end_game = EndGame(game_data, blitz_manager, DummyScoreManager())

    winners = end_game.get_winners()

    assert end_game.get_winner() is None
    assert end_game.is_draw() is True
    assert [player.get_username() for player in winners] == ["Alice", "Bob"]


def test_end_game_get_winners_returns_empty_list_when_no_players() -> None:
    game_data, blitz_manager = create_game_data(empty=False, playable=True)
    game_data.players = {}
    end_game = EndGame(game_data, blitz_manager, DummyScoreManager())

    assert end_game.get_winners() == []
    assert end_game.get_winner() is None
    assert end_game.is_draw() is False


def test_score_value_supports_get_score_and_score_attribute_variants() -> None:
    get_score_obj = DummyPlayerWithGetScore(DummyPlayerScoreObject(9))
    get_score_number = DummyPlayerWithGetScore(8.6)
    score_attr_obj = DummyPlayerWithScoreAttr(DummyPlayerScoreObject(7))
    score_attr_number = DummyPlayerWithScoreAttr(6.4)
    no_score = object()

    assert EndGame._score_value(get_score_obj) == 9
    assert EndGame._score_value(get_score_number) == 8
    assert EndGame._score_value(score_attr_obj) == 7
    assert EndGame._score_value(score_attr_number) == 6
    assert EndGame._score_value(no_score) == 0
