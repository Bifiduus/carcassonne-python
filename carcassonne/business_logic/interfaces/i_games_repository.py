from abc import ABC, abstractmethod
from sqlite3 import Row
from typing import Any


class IGamesRepository(ABC):

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def get_next_available_id(self) -> int:
        pass

    @abstractmethod
    def party_is_launched(self, host_id) -> bool:
        pass

    @abstractmethod
    def is_accounted_for(self) -> bool:
        pass

    @abstractmethod
    def get_password(self, player_id: int) -> str:
        pass

    @abstractmethod
    def get_online_player(self, server: str) -> str:
        pass

    @abstractmethod
    def registering(self, username: str, password: str) -> bool:
        pass

    @abstractmethod
    def player_exists(self, player_name: str) -> bool:
        pass

    @abstractmethod
    def check_all_invitations_timeout(self, timeout: float) -> list[int]:
        pass

    @abstractmethod
    def get_player_profile(self, player_id: int) -> dict[str, Any]:
        pass

    @abstractmethod
    def is_database_closed(self) -> bool:
        pass

    @abstractmethod
    def reopen(self):
        pass

    @abstractmethod
    def change_status(self, client_id: str, status: str) -> str:
        pass

    @abstractmethod
    def current_players(self) -> str:
        pass

    @abstractmethod
    def get_parties(self) -> list[int]:
        pass

    @abstractmethod
    def check_party_is_alive(self, group_id: int) -> bool:
        pass

    @abstractmethod
    def get_group_from_game(self, game_id: int) -> int:
        pass

    @abstractmethod
    def delete_party(self, party_id: int):
        pass

    @abstractmethod
    def create_game(self, game_name: str, group_id: int):
        pass

    @abstractmethod
    def get_game_id(self, group_id: int) -> int:
        pass

    @abstractmethod
    def get_host_from_party(self, party_id: int) -> int:
        pass

    @abstractmethod
    def invitation_received(self, client_id: str) -> tuple[int, int]:
        pass

    @abstractmethod
    def accept_invitation(self, group_id: int, invited: str):
        pass

    @abstractmethod
    def get_game(self, client_id: str) -> int:
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
    def send_invitation(
        self, invited_player: str, invitee_player: str
    ) -> bool:
        pass

    @abstractmethod
    def invitation_sent_from(self, client_id: str) -> bool:
        pass

    @abstractmethod
    def get_id_from_username(self, player_username: str) -> int:
        pass

    @abstractmethod
    def cancel_invitation_from(
        self, client_id: str, players: list[str]
    ) -> str:
        pass

    @abstractmethod
    def get_party(self, client_id: str) -> list[int]:
        pass

    @abstractmethod
    def create_default_online_player(
        self, username: str, password: str, server: str
    ) -> str:
        pass

    @abstractmethod
    def get_players_from_group(self, group_id: int) -> list[str]:
        pass

    @abstractmethod
    def reject_invitation(self, invited: str):
        pass

    @abstractmethod
    def create_party(self, client_username: str) -> int | None:
        pass

    @abstractmethod
    def set_new_username_for_server(self, server: str, username: str):
        pass

    @abstractmethod
    def has_no_special_username(self, server: str) -> bool:
        pass

    @abstractmethod
    def client_quit(self, client_username: str):
        pass

    @abstractmethod
    def get_party_id(self, client_id: str) -> int:
        pass

    @abstractmethod
    def clean_party(self, party: int):
        pass

    @abstractmethod
    def close(self):
        pass
