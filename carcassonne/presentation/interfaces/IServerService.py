"""Module providing an interface between Présentation and Logique Métier"""
from abc import ABC, abstractmethod
from typing import Any

from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData


class IServerService(ABC):
    # pylint: disable=missing-class-docstring
    @abstractmethod
<<<<<<< HEAD:carcassonne/presentation/interfaces/IServerService.py
    def list_available_servers(self, timeout: float = 5.0) -> list[int]:
        pass

    @abstractmethod
    def is_server_running(self) -> bool:
        pass

    @abstractmethod
    def server_start(self, port: str = "12345"):
        pass

    @abstractmethod
    def create_online_player(self, username: str) -> str:
=======
    def list_available_servers(self, timeout: float = 5.0) -> list[str]:
        pass

    @abstractmethod
    def server_start(self, port: int = 12345):
>>>>>>> 8155e29 (implemented cli taking charge of server commands ( start, stop, ... )):src/carcassonne/Presentation/Interfaces/IServerService.py
        pass

    @abstractmethod
    def server_stop(self):
        pass

    @abstractmethod
<<<<<<< HEAD:carcassonne/presentation/interfaces/IServerService.py
    def server_quit(self) -> int:
=======
    def server_quit(self):
>>>>>>> 8155e29 (implemented cli taking charge of server commands ( start, stop, ... )):src/carcassonne/Presentation/Interfaces/IServerService.py
        pass

    @abstractmethod
    def ping(self) -> str:
        pass

    @abstractmethod
<<<<<<< HEAD:carcassonne/presentation/interfaces/IServerService.py
    def connected_to_a_server(self) -> bool:
        pass

    @abstractmethod
    def join_server(self, ip: str | None = None, port: int | None = None, timeout: float = 5.0) -> bool:
        pass

    @abstractmethod
    def send_to_server(self, text: str) -> bool:
        pass
=======
    def join_server(self, ip: str | None = None, port: int | None = None, timeout: float = 5.0) -> bool:
        pass
>>>>>>> 8155e29 (implemented cli taking charge of server commands ( start, stop, ... )):src/carcassonne/Presentation/Interfaces/IServerService.py
