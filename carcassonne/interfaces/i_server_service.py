from abc import ABC, abstractmethod


class IServerService(ABC):
    @abstractmethod
    def is_server_running(self) -> bool:
        pass

    @abstractmethod
    def server_start(self, port: str = "12345"):
        pass

    @abstractmethod
    def server_stop(self):
        pass

    @abstractmethod
    def number_current_games(self) -> int:
        pass

    @abstractmethod
    def get_connected_players(self) -> list[dict[str, str]]:
        pass

    @abstractmethod
    def start_new_game_with_players(self, player_ids: list[str]) -> str:
        pass
