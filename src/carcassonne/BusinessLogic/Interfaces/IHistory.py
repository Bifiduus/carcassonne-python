from abc import ABC, abstractmethod


class IHistory(ABC):

    @abstractmethod
    def clear_history(self) -> None:
        pass