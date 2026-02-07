from abc import ABC, abstractmethod

class ITilesInfo(ABC):
    # pylint: disable=missing-class-docstring
    @abstractmethod
    def is_tile_left(self, tile_code: str) -> bool:
        pass

    @abstractmethod
    def remove_tile(self, tile_code: str) -> None:
        pass