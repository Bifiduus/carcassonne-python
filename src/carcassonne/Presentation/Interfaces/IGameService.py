"""Module providing an interface between Présentation and Logique Métier"""
from abc import ABC, abstractmethod

from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData

class IGameService(ABC):
    # pylint: disable=missing-class-docstring
    @abstractmethod
    def start_new_game(self):
        pass

    @abstractmethod
    def play_move(self, move):
        pass

    @abstractmethod
    def get_game_configuration(self) -> dict :
        pass
