"""Module providing an interface between Présentation and Logique Métier"""
from abc import ABC, abstractmethod
from typing import Any


class IGameService(ABC):
    # pylint: disable=missing-class-docstring
    @abstractmethod
    def start_new_game(self) -> None:
        pass

    @abstractmethod
    def play_move(self, move: str) -> bool:
        pass

    @abstractmethod
    def undo(self) -> None:
        pass

    @abstractmethod
    def redo(self) -> None:
        pass

    @abstractmethod
    def get_history(self) -> list:
        pass

    @abstractmethod
    def get_game_configuration(self) -> dict:
        pass

    @abstractmethod
    def is_undo_history_empty(self) -> bool:
        pass

    @abstractmethod
    def clear_undo_history(self) -> None:
        pass

    @abstractmethod
    def get_board(self) -> list[Any] | None:
        pass

    @abstractmethod
    def shuffle_deck(self, algo: str | None = None, seed: int | None = None) -> int:
        pass

    @abstractmethod
    def draw_tile(self) -> str | None:
        pass

    @abstractmethod
    def get_board_data(self) -> list[dict] | None:
        pass

    @abstractmethod
    def get_tile_data(self, tile: str) -> None:
        pass

    @abstractmethod
    def get_close_neighbors(self, x: int, y: int) -> tuple[int | None, int | None]:
        pass

    @abstractmethod
    def get_meeples_data(self) -> list[dict]:
        pass
