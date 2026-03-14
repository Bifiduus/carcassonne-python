"""Module providing an interface between Présentation and Logique Métier"""
from abc import ABC, abstractmethod
from typing import Any

from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData


class IServerService(ABC):
    # pylint: disable=missing-class-docstring
    @abstractmethod
    def list_available_servers(self, timeout: float = 5.0) -> list[str]:
        pass

    @abstractmethod
    def server_start(self, port: int = 12345):
        pass

    @abstractmethod
    def server_stop(self):
        pass

    @abstractmethod
    def server_quit(self):
        pass

    @abstractmethod
    def ping(self) -> str:
        pass

    @abstractmethod
    def join_server(self, ip: str | None = None, port: int | None = None, timeout: float = 5.0) -> bool:
        pass
