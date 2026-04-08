from abc import ABC, abstractmethod
from typing import Any


class IHistory(ABC):

    past_moves: list[Any]
    future_moves: list[Any]

    @abstractmethod
    def push_past(self, record: Any) -> None:
        pass

    @abstractmethod
    def push_future(self, record: Any) -> None:
        pass

    @abstractmethod
    def pop_past(self) -> Any:
        pass

    @abstractmethod
    def pop_future(self) -> Any:
        pass

    @abstractmethod
    def clear_future(self) -> None:
        pass

    @abstractmethod
    def clear_history(self) -> None:
        pass

    @abstractmethod
    def list_history(self) -> list[str]:
        pass
