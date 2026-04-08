from abc import ABC, abstractmethod


class IClientMessageVisitor(ABC):
    @abstractmethod
    def visit_server_message(self, message: str, server: str) -> None:
        pass
