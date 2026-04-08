from abc import ABC, abstractmethod


class IMeeple(ABC):
    player_id: int
    tile_id: int
    position: int
    lands_components: str

    @abstractmethod
    def get_position_label(self) -> str:
        pass
