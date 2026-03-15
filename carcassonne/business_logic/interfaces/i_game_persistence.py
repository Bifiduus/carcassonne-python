"""Module providing an interface between Logique Métier and Données"""

from abc import ABC, abstractmethod


class IGamePersistence(ABC):
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
