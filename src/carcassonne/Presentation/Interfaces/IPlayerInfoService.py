"""Module providing an interface between Présentation and Logique Métier"""
from abc import ABC, abstractmethod
from typing import Any

from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData
from carcassonne.BusinessLogic.Player import Player
from carcassonne.BusinessLogic.ScoreManager import PlayerScore

class IPlayerInfoService(ABC):  

    @abstractmethod  
    def get_id(self) -> int:
        pass
    @abstractmethod  
    def get_username(self) -> str:
        pass
    @abstractmethod  
    def get_score(self) -> PlayerScore:
        pass
    @abstractmethod  
    def get_color(self) -> str:
        pass
    @abstractmethod  
    def is_ai_player(self) -> bool:
        pass

    @abstractmethod
    def get_number_of_players(self) -> int:
        pass

    @abstractmethod
    def get_current_player(self) -> Player:
        pass

    @abstractmethod
    def get_score_int(self) -> int :
        pass