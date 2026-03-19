"""Module providing an interface between Présentation and Logique Métier"""
from abc import ABC, abstractmethod
from typing import Any

from carcassonne.business_logic.interfaces.i_graph_data import IGraphData


class IServerService(ABC):
    # pylint: disable=missing-class-docstring
    @abstractmethod
    def list_available_servers(self, timeout: float = 5.0) -> dict[str, int]:
        pass

    @abstractmethod
    def is_server_running(self) -> bool:
        pass

    @abstractmethod
    def server_start(self, port: str = "12345"):
        pass

    @abstractmethod
    def create_online_player(self, username: str) -> str:
        pass

    @abstractmethod
    def server_stop(self):
        pass

    @abstractmethod
    def server_quit(self) -> int:
        pass

    @abstractmethod
    def ping(self) -> str:
        pass

    @abstractmethod
    def connected_to_a_server(self) -> bool:
        pass

    @abstractmethod
    def join_server(self, ip: str | None = None, port: int | None = None, timeout: float = 5.0) -> bool:
        pass

    @abstractmethod
    def send_to_server(self, text: str) -> bool:
        pass
