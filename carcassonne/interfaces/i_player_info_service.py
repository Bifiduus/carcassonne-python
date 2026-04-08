"""Module providing an interface between Presentation and Business Logic."""

from abc import ABC, abstractmethod

from carcassonne.interfaces.i_player import IPlayer
from carcassonne.interfaces.i_player_score import IPlayerScore


class IPlayerInfoService(ABC):

    @abstractmethod
    def get_id(self) -> int:
        pass

    @abstractmethod
    def get_username(self) -> str:
        pass

    @abstractmethod
    def get_score(self) -> IPlayerScore:
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
    def get_current_player(self) -> IPlayer:
        pass

    @abstractmethod
    def get_score_int(self) -> int:
        pass

    @abstractmethod
    def get_meeples(self) -> int:
        pass
