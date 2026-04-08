from abc import ABC, abstractmethod
from typing import Any

from carcassonne.interfaces.i_player import IPlayer


class IGameService(ABC):
    @abstractmethod
    def start_new_game(self) -> None:
        pass

    @abstractmethod
    def play_move(self, move: str) -> bool:
        pass

    @abstractmethod
    def parse_move(self, move: str) -> dict:
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
    def save_config(self) -> None:
        pass

    @abstractmethod
    def set_game_configuration(self, key: str, value) -> None:
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
    def shuffle_deck(
        self, algo: str | None = None, seed: int | None = None
    ) -> int:
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
    def get_current_player(self) -> IPlayer:
        pass

    @abstractmethod
    def get_players_order(self) -> list[int]:
        pass

    @abstractmethod
    def get_all_players(self) -> list[IPlayer]:
        pass

    @abstractmethod
    def play_ai_turn(self, game=None):
        pass

    @abstractmethod
    def get_close_neighbors(
        self, x: int, y: int
    ) -> tuple[int | None, int | None]:
        pass

    @abstractmethod
    def get_adjacent_position(
        self, vertex_id: int, side: int
    ) -> tuple[int, int] | None:
        pass

    @abstractmethod
    def get_meeples_data(self) -> list[dict]:
        pass

    @abstractmethod
    def end_game(self) -> bool:
        pass

    @abstractmethod
    def get_winners(self) -> list[IPlayer]:
        pass

    @abstractmethod
    def get_winner(self) -> IPlayer | None:
        pass

    @abstractmethod
    def is_draw(self) -> bool:
        pass

    @abstractmethod
    def provide_hint(self) -> str:
        pass

    @abstractmethod
    def tick_blitz(self) -> bool:
        pass

    @abstractmethod
    def get_timeout_message(self) -> str:
        pass

    @abstractmethod
    def get_current_player_remaining_time_seconds(self) -> float | None:
        pass

    @abstractmethod
    def get_player_remaining_time_seconds(
        self, player_id: int
    ) -> float | None:
        pass

    @abstractmethod
    def get_all_players_remaining_time_seconds(
        self,
    ) -> list[tuple[int, float]]:
        pass
