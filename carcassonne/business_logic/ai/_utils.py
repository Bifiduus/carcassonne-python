"""Shared helpers used across AI player modules."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from carcassonne.business_logic.game.game import Game


def _is_river_tile(tile: str | None) -> bool:
    """Return True when a tile belongs to the river deck."""
    return bool(tile) and "S" in tile


def _discard_unplayable_tile(game: "Game", tile: str | None) -> None:
    """Put an unplayable tile back at the bottom of its source deck."""
    if tile is None:
        return
    if _is_river_tile(tile):
        game.game_data.deck.river_tiles.append(tile)
    else:
        game.game_data.deck.append(tile)


def _restore_drawn_tile_after_undo(
    game: "Game", tile: str | None
) -> None:
    """Restore a drawn tile to the top of its source deck for undo."""
    if tile is None:
        return
    if _is_river_tile(tile):
        game.game_data.deck.river_tiles.insert(0, tile)
    else:
        game.game_data.deck.tiles.append(tile)
