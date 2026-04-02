from abc import ABC, abstractmethod


class IClientMessageVisitor(ABC):
    """Visitor interface for routes from Client to GUI/UI."""

    @abstractmethod
    def visit_server_message(self, message: str, server: str) -> None:
        pass
