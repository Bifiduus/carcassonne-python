from abc import ABC, abstractmethod


class ITilesInfo(ABC):
    # pylint: disable=missing-class-docstring
    direction_dict: dict[str, int]
    tiles_count: dict[str, int]
    meeple_placement_list: list[str]

    @abstractmethod
    def is_tile_left(self, tile_code: str) -> bool:
        pass

    @abstractmethod
    def remove_tile(self, tile_code: str) -> None:
        pass

    @abstractmethod
    def add_tile(self, tile_code: str) -> None:
        pass
