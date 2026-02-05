
from dataclasses import dataclass


@dataclass
class GameRepository:

    play_history: list
    undo_history: list

    def __init__(self):
        self.play_history = []
        self.undo_history = []