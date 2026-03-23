"""Module providing an interface between Présentation and Logique Métier"""
from abc import ABC, abstractmethod


class IServerService(ABC):
    # pylint: disable=missing-class-docstring

    @abstractmethod
    def is_server_running(self) -> bool:
        pass

    @abstractmethod
    def server_start(self, port: str = "12345"):
        pass

    @abstractmethod
    def server_stop(self):
        pass
