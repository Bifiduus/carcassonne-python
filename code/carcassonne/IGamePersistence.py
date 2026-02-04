"""Module providing an interface between Logique Métier and Données"""
from abc import ABC, abstractmethod

class IGameService(ABC):
    # pylint: disable=missing-class-docstring
    @abstractmethod
    def save(self):
        pass

    @abstractmethod
    def load(self):
        pass

    @abstractmethod
    def serialize(self):
        pass

    @abstractmethod
    def invite(self):
        pass
