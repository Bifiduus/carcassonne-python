
from dataclasses import dataclass


@dataclass
class GameRepository:

    def __init__(self) -> None:
        self.game_state = None
