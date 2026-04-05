from types import SimpleNamespace

from carcassonne.business_logic.ai._utils import (
    _discard_unplayable_tile,
    _is_river_tile,
    _restore_drawn_tile_after_undo,
)


class DummyDeck:
    def __init__(self) -> None:
        self.tiles: list[str] = []
        self.river_tiles: list[str] = []
        self.append_calls: list[str] = []

    def append(self, tile: str) -> None:
        self.append_calls.append(tile)
        self.tiles = [tile] + self.tiles


def create_game() -> SimpleNamespace:
    return SimpleNamespace(game_data=SimpleNamespace(deck=DummyDeck()))


def test_is_river_tile_only_matches_tiles_with_sides_marked_s() -> None:
    assert _is_river_tile(None) is False
    assert _is_river_tile("CFFF") is False
    assert _is_river_tile("FSFS") is True


def test_discard_unplayable_tile_puts_tiles_back_in_their_source_deck() -> None:
    game = create_game()

    _discard_unplayable_tile(game, "CFFF")
    _discard_unplayable_tile(game, "FSFS")
    _discard_unplayable_tile(game, None)

    assert game.game_data.deck.append_calls == ["CFFF"]
    assert game.game_data.deck.tiles == ["CFFF"]
    assert game.game_data.deck.river_tiles == ["FSFS"]


def test_restore_drawn_tile_after_undo_restores_base_and_river_order() -> None:
    game = create_game()
    game.game_data.deck.tiles = ["CRRF"]
    game.game_data.deck.river_tiles = ["RSRS"]

    _restore_drawn_tile_after_undo(game, "CFFF")
    _restore_drawn_tile_after_undo(game, "FSFS")
    _restore_drawn_tile_after_undo(game, None)

    assert game.game_data.deck.tiles == ["CRRF", "CFFF"]
    assert game.game_data.deck.river_tiles == ["FSFS", "RSRS"]
