from abc import ABC, abstractmethod


class IPlayerScore(ABC):
    score: int

    @abstractmethod
    def add_score(self, score: int) -> None:
        pass

    @abstractmethod
    def set_points(self, points: int) -> None:
        pass
