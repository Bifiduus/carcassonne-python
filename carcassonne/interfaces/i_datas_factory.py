from abc import ABC, abstractmethod
from typing import Any


class IDatasFactory(ABC):
    @abstractmethod
    def create(self, class_name: str, *args: Any, **kwargs: Any) -> Any:
        pass

    @abstractmethod
    def available_classes(self) -> list[str]:
        pass
