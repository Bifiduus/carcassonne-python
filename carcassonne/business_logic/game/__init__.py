"""Public exports for the game package."""

from typing import TYPE_CHECKING

__all__ = ["Game"]

if TYPE_CHECKING:
    from .game import Game


def __getattr__(name: str):
    if name == "Game":
        from .game import Game

        return Game
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
