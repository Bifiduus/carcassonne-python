from carcassonne.business_logic.game.deck_manager import DeckManager
from carcassonne.datas.seed import Seed


class DummyDatasFactory:
    def create(self, class_name: str, *args, **kwargs):
        if class_name == "Seed":
            return Seed(*args, **kwargs)
        raise ValueError(f"Unknown class {class_name}")

    def available_classes(self):
        return ["Seed"]


class DummyDeck:
    def __init__(self, draw_tile=None, draw_river_tile=None) -> None:
        self._draw_tile = draw_tile
        self._draw_river_tile = draw_river_tile
        self._draw_sequence: list[str | None] = []
        self.draw_calls: list[bool] = []
        self.draw_river_calls: list[bool] = []
        self.shuffle_naive_calls: list[int] = []
        self.shuffle_fisher_yates_calls: list[int] = []
        self.append_calls: list[str] = []
        self.tiles: list[str] = []
        self.river_tiles: list[str] = []

    def draw(self, silent: bool = False):
        self.draw_calls.append(silent)
        if self._draw_sequence:
            return self._draw_sequence.pop(0)
        return self._draw_tile

    def draw_river_tile(self, silent: bool = False):
        self.draw_river_calls.append(silent)
        return self._draw_river_tile

    def append(self, tile: str) -> None:
        self.append_calls.append(tile)

    def len(self) -> int:
        return len(self.tiles) if self.tiles else 1

    def len_river(self) -> int:
        return len(self.river_tiles) if self.river_tiles else 1

    def shuffle_naive(self, seed: int) -> None:
        self.shuffle_naive_calls.append(seed)

    def shuffle_fisher_yates(self, seed: int) -> None:
        self.shuffle_fisher_yates_calls.append(seed)


class DummyGameData:
    def __init__(
        self,
        deck: DummyDeck,
        current_hand=None,
        river_over: bool = False,
        shuffle_algo: str = "fisher-yates",
        default_seed=None,
    ) -> None:
        self.deck = deck
        self.current_hand = current_hand
        self._river_over = river_over
        self.shuffle_algo = shuffle_algo
        self.default_seed = default_seed
        self.seed = None
        self._end_game_scored = False
        self.no_playable_tiles_remaining = False

        # Optional collaborators for playable-tile checks.
        self.rules_manager = None
        self.graph = None
        self.tiles_info = None
        self._player = None

    def is_river_over(self) -> bool:
        return self._river_over

    def get_current_player(self):
        return self._player


class DummyPlayer:
    def __init__(self, player_id: int = 0) -> None:
        self.player_id = player_id

    def get_id(self) -> int:
        return self.player_id


class DummyVertex:
    def is_neighbor_free(self, side: int) -> bool:
        del side
        return True


class DummyGraph:
    def get_vertices(self):
        return {0: DummyVertex()}


class DummyTilesInfo:
    direction_dict = {"N": 0, "E": 1, "S": 2, "W": 3}


class DummyRulesManager:
    def __init__(self, playable_tiles: set[str]) -> None:
        self.playable_tiles = playable_tiles

    def check_move(self, move, graph, river_manager, current_player_id):
        del graph, river_manager, current_player_id
        tile_prefix = move.rsplit("/", 1)[0]
        return tile_prefix in self.playable_tiles


class DummyBlitzManager:
    def __init__(
        self, timed_out_now: bool = False, current_player_playable: bool = True
    ) -> None:
        self.timed_out_now = timed_out_now
        self.current_player_playable = current_player_playable

    def tick_blitz(self) -> bool:
        return self.timed_out_now

    def _ensure_current_player_playable(self) -> bool:
        return self.current_player_playable


class DummyRiverManager:
    def __init__(self, active: bool) -> None:
        self.active = active

    def is_river_active(self) -> bool:
        return self.active


def test_draw_tile_returns_none_when_blitz_times_out() -> None:
    deck = DummyDeck(draw_tile="CFFF")
    game_data = DummyGameData(deck)
    manager = DeckManager(
        game_data,
        DummyBlitzManager(timed_out_now=True),
        DummyRiverManager(active=False),
        DummyDatasFactory(),
    )

    assert manager.draw_tile() is None
    assert deck.draw_calls == []
    assert game_data.current_hand is None


def test_draw_tile_returns_none_when_current_player_cannot_play() -> None:
    deck = DummyDeck(draw_tile="CFFF")
    game_data = DummyGameData(deck)
    manager = DeckManager(
        game_data,
        DummyBlitzManager(current_player_playable=False),
        DummyRiverManager(active=False),
        DummyDatasFactory(),
    )

    assert manager.draw_tile() is None
    assert deck.draw_calls == []


def test_draw_tile_reuses_current_hand_without_drawing() -> None:
    deck = DummyDeck(draw_tile="CFFF")
    game_data = DummyGameData(deck, current_hand="CRRF")
    manager = DeckManager(
        game_data,
        DummyBlitzManager(),
        DummyRiverManager(active=False),
        DummyDatasFactory(),
    )

    assert manager.draw_tile() == "CRRF"
    assert deck.draw_calls == []


def test_draw_tile_uses_river_deck_when_river_is_active() -> None:
    deck = DummyDeck(draw_tile="CFFF", draw_river_tile="FSFS")
    game_data = DummyGameData(deck, river_over=False)
    manager = DeckManager(
        game_data,
        DummyBlitzManager(),
        DummyRiverManager(active=True),
        DummyDatasFactory(),
    )

    assert manager.draw_tile(silent=True) == "FSFS"
    assert deck.draw_river_calls == [True]
    assert deck.draw_calls == []
    assert game_data.current_hand == "FSFS"


def test_draw_tile_falls_back_to_base_deck_when_river_is_over() -> None:
    deck = DummyDeck(draw_tile="CCFF", draw_river_tile="FSFS")
    game_data = DummyGameData(deck, river_over=True)
    manager = DeckManager(
        game_data,
        DummyBlitzManager(),
        DummyRiverManager(active=True),
        DummyDatasFactory(),
    )

    assert manager.draw_tile() == "CCFF"
    assert deck.draw_calls == [False]
    assert deck.draw_river_calls == []
    assert game_data.current_hand == "CCFF"


def test_draw_tile_keeps_hand_empty_when_source_deck_is_empty() -> None:
    deck = DummyDeck(draw_tile=None)
    game_data = DummyGameData(deck)
    manager = DeckManager(
        game_data,
        DummyBlitzManager(),
        DummyRiverManager(active=False),
        DummyDatasFactory(),
    )

    assert manager.draw_tile() is None
    assert game_data.current_hand is None


def test_draw_tile_redraws_when_current_hand_is_unplayable() -> None:
    deck = DummyDeck()
    deck._draw_sequence = ["PLAY"]
    deck.tiles = ["PLAY"]
    game_data = DummyGameData(deck, current_hand="BLOCKED")
    game_data.rules_manager = DummyRulesManager({"PLAY"})
    game_data.graph = DummyGraph()
    game_data.tiles_info = DummyTilesInfo()
    game_data._player = DummyPlayer(1)
    manager = DeckManager(
        game_data,
        DummyBlitzManager(),
        DummyRiverManager(active=False),
        DummyDatasFactory(),
    )

    assert manager.draw_tile() == "PLAY"
    assert game_data.current_hand == "PLAY"
    assert deck.append_calls == ["BLOCKED"]


def test_draw_tile_redraws_until_playable_tile_is_found() -> None:
    deck = DummyDeck()
    deck._draw_sequence = ["BAD1", "GOOD"]
    deck.tiles = ["BAD1", "GOOD"]
    game_data = DummyGameData(deck)
    game_data.rules_manager = DummyRulesManager({"GOOD"})
    game_data.graph = DummyGraph()
    game_data.tiles_info = DummyTilesInfo()
    game_data._player = DummyPlayer(1)
    manager = DeckManager(
        game_data,
        DummyBlitzManager(),
        DummyRiverManager(active=False),
        DummyDatasFactory(),
    )

    assert manager.draw_tile() == "GOOD"
    assert game_data.current_hand == "GOOD"
    assert deck.append_calls == ["BAD1"]


def test_draw_tile_ends_game_when_all_remaining_tiles_are_unplayable() -> None:
    deck = DummyDeck()
    deck._draw_sequence = ["BAD1", "BAD2"]
    deck.tiles = ["BAD1", "BAD2"]
    game_data = DummyGameData(deck)
    game_data.rules_manager = DummyRulesManager(set())
    game_data.graph = DummyGraph()
    game_data.tiles_info = DummyTilesInfo()
    game_data._player = DummyPlayer(1)
    manager = DeckManager(
        game_data,
        DummyBlitzManager(),
        DummyRiverManager(active=False),
        DummyDatasFactory(),
    )

    assert manager.draw_tile(silent=True) is None
    assert game_data.current_hand is None
    assert game_data.no_playable_tiles_remaining is True
    assert deck.append_calls == ["BAD1", "BAD2"]


def test_shuffle_deck_uses_configured_default_seed_for_naive_shuffle() -> None:
    deck = DummyDeck()
    game_data = DummyGameData(
        deck,
        shuffle_algo="naive",
        default_seed=1234,
    )
    manager = DeckManager(
        game_data,
        DummyBlitzManager(),
        DummyRiverManager(active=False),
        DummyDatasFactory(),
    )

    seed = manager.shuffle_deck()

    assert seed == 1234
    assert deck.shuffle_naive_calls == [1234]
    assert deck.shuffle_fisher_yates_calls == []
    assert game_data.seed == 1234


def test_shuffle_deck_generates_seed_when_missing() -> None:
    class FakeDatasFactory:
        def create(self, class_name: str, *args, **kwargs):
            if class_name == "Seed":
                obj = Seed(*args, **kwargs)
                obj.seed = 9876
                return obj
            raise ValueError(f"Unknown class {class_name}")

        def available_classes(self):
            return ["Seed"]

    deck = DummyDeck()
    game_data = DummyGameData(deck, shuffle_algo="fisher-yates")
    manager = DeckManager(
        game_data,
        DummyBlitzManager(),
        DummyRiverManager(active=False),
        FakeDatasFactory(),
    )

    seed = manager.shuffle_deck()

    assert seed == 9876
    assert deck.shuffle_fisher_yates_calls == [9876]
    assert deck.shuffle_naive_calls == []
    assert game_data.seed == 9876


def test_shuffle_deck_seeds_runtime_rng_with_resolved_seed(
    monkeypatch,
) -> None:
    deck = DummyDeck()
    game_data = DummyGameData(
        deck,
        shuffle_algo="fisher-yates",
        default_seed=1234,
    )
    manager = DeckManager(
        game_data,
        DummyBlitzManager(),
        DummyRiverManager(active=False),
        DummyDatasFactory(),
    )
    seeded_values: list[int] = []

    monkeypatch.setattr(
        "carcassonne.business_logic.game.deck_manager.random.seed",
        lambda value: seeded_values.append(value),
    )

    manager.shuffle_deck()

    assert seeded_values == [1234]
