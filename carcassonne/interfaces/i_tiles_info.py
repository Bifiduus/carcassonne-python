from abc import ABC, abstractmethod

from carcassonne.interfaces.i_tile import ITile


class ITilesInfo(ABC):
    # pylint: disable=missing-class-docstring
    direction_dict: dict[str, int]
    tiles_count: dict[str, int]
    tiles_dict: dict[str, list[str]]
    meeple_placement_list: list[str]
    direction_matrix: list[list[list[str]]]

    @abstractmethod
    def is_tile_left(self, tile_code: str) -> bool:
        pass

    @abstractmethod
    def remove_tile(self, tile_code: str) -> None:
        pass

    @abstractmethod
    def add_tile(self, tile_code: str) -> None:
        pass

    @abstractmethod
    def get_tile_definition(self, tile_code: str) -> ITile | None:
        pass

    @abstractmethod
    def get_direction_matrix(self) -> list[list[list[str]]]:
        pass
