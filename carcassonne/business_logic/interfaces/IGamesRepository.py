from abc import ABC, abstractmethod
from sqlite3 import Row
from typing import Any, List


class IGamesRepository(ABC):

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
<<<<<<< HEAD:carcassonne/business_logic/interfaces/IGamesRepository.py
    def get_next_available_id(self) -> int:
        pass

    @abstractmethod
    def is_accounted_for(self) -> bool:
        pass

    @abstractmethod
    def get_online_player(self) -> str:
        pass

    @abstractmethod
=======
>>>>>>> d495553 (added OnlineCommunication to ease the reading of Server.py, plus implementation of IGamesRepository):src/carcassonne/BusinessLogic/Interfaces/IGamesRepository.py
    def player_exists(self, player_name: str) -> bool:
        pass

    @abstractmethod
<<<<<<< HEAD:carcassonne/business_logic/interfaces/IGamesRepository.py
    def check_all_invitations_timeout(self, timeout: float):
        pass

    @abstractmethod
=======
>>>>>>> d495553 (added OnlineCommunication to ease the reading of Server.py, plus implementation of IGamesRepository):src/carcassonne/BusinessLogic/Interfaces/IGamesRepository.py
    def get_player_profile(self, player_id: int) -> dict[str, Any]:
        pass

    @abstractmethod
<<<<<<< HEAD:carcassonne/business_logic/interfaces/IGamesRepository.py
    def is_database_closed(self) -> bool:
        pass

    @abstractmethod
    def reopen(self):
        pass

    @abstractmethod
    def change_status(self, client_username: str, status: str) -> str:
=======
    def change_status(self, client_id: str, status: str) -> str:
>>>>>>> d495553 (added OnlineCommunication to ease the reading of Server.py, plus implementation of IGamesRepository):src/carcassonne/BusinessLogic/Interfaces/IGamesRepository.py
        pass

    @abstractmethod
    def current_players(self) -> str:
        pass

    @abstractmethod
    def invitation_received(self, client_id: str) -> Row:
        pass

    @abstractmethod
<<<<<<< HEAD:carcassonne/business_logic/interfaces/IGamesRepository.py
    def accept_invitation(self, group_id: int, invited: str):
        pass

    @abstractmethod
    def get_game(self, client_id: str) -> Row:
        pass

    @abstractmethod
    def check_all_invitations_resolved(self, client_id: str) -> bool:
        pass

    @abstractmethod
    def get_scoreboard(self) -> list[Row]:
        pass

    @abstractmethod
    def get_username(self, player_id: str) -> str:
        pass

    @abstractmethod
    def send_invitation(self, invited_player: str, invitee_player: str) -> bool:
=======
    def accept_invitation(self, party_id: int, invited: str):
        pass

    @abstractmethod
    def get_game(self, client_id: int) -> Row:
        pass

    @abstractmethod
    def check_all_invitations_resolved(self, client_id: int) -> bool:
        pass

    @abstractmethod
    def get_scoreboard(self) -> str:
>>>>>>> d495553 (added OnlineCommunication to ease the reading of Server.py, plus implementation of IGamesRepository):src/carcassonne/BusinessLogic/Interfaces/IGamesRepository.py
        pass

    @abstractmethod
    def invitation_sent_from(self, client_id: str) -> bool:
        pass

    @abstractmethod
<<<<<<< HEAD:carcassonne/business_logic/interfaces/IGamesRepository.py
    def cancel_invitation_from(self, client_id: str, players: list[str]) -> str:
        pass

    @abstractmethod
    def create_party(self, name: str, player_names: list[str], client_username: str) -> int | None:
        pass

    @abstractmethod
    def get_party(self, client_id: str) -> list[str]:
        pass

    @abstractmethod
    def create_online_player(self, username: str) -> str:
        pass

    @abstractmethod
    def get_party_name(self, client_id: str) -> str:
=======
    def cancel_invitation_from(self, client_id: str) -> str:
        pass

    @abstractmethod
    def create_party(self, name: str, player_names: list[str], host_id: int) -> int | None:
        pass

    @abstractmethod
    def get_party(self, host_id) -> list[str]:
        pass

    @abstractmethod
    def get_party_name(self, host_id: int) -> str:
>>>>>>> d495553 (added OnlineCommunication to ease the reading of Server.py, plus implementation of IGamesRepository):src/carcassonne/BusinessLogic/Interfaces/IGamesRepository.py
        pass

    @abstractmethod
    def close(self):
        pass
