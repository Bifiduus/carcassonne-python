"""Module providing an interface between Présentation and Logique Métier"""
from abc import ABC, abstractmethod


class IClientService(ABC):

    @abstractmethod
    def list_available_servers(self, timeout: float = 5.0) -> dict[str, int]:
        pass

    @abstractmethod
    def create_default_online_player(self, username: str, password: str,
                                     server: str = "127.0.1.1") -> str:
        pass

    @abstractmethod
    def ping(self) -> str:
        pass

    @abstractmethod
    def connected_to_a_server(self) -> bool:
        pass

    @abstractmethod
    def join_server(self, ip: str | None = None, port: int | None = None,
                    timeout: float = 5.0) -> bool:
        pass

    @abstractmethod
    def send_to_server(self, text: str) -> bool:
        pass

    @abstractmethod
    def disconnect(self):
        pass
