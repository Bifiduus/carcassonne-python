"""Module providing an interface between Présentation and Logique Métier"""
from abc import ABC, abstractmethod

class IGameService(ABC):
    # pylint: disable=missing-class-docstring
    @abstractmethod
    def placeTile(self, move):
        pass

    @abstractmethod
    def placeMeeple(self, move):
        pass

    @abstractmethod
    def getGameStates(self):
        pass

    @abstractmethod
    def playAI(self):
        pass
