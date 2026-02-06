"""This module defines the Game class, which implements the IGameService interface. 
The Game class is responsible for managing the game state, including the play history and undo history. It interacts with the RulesEngine to determine if the current player is human and with the GameRepository to store and retrieve game data.
"""
from typing import Any, List

from carcassonne.BusinessLogic.RulesEngine import RulesEngine
from carcassonne.Datas.GameRepository import GameRepository
from carcassonne.Datas.GraphData import GraphData
from carcassonne.IGameService import IGameService
from .AIModel import is_ai_player

class Game(IGameService):
    def __init__(self, data: Any) -> None:
        self.data: Any = data
        self.rules_engine: RulesEngine = RulesEngine(data)
        self.game_repository: GameRepository = GameRepository()
        self.graph: GraphData = GraphData()
        self.play_history: List[Any] = self.game_repository.play_history
        self.undo_history: List[Any] = self.game_repository.undo_history

    def start_new_game(self):
        self.play_history.clear()
        self.undo_history.clear()
        self.graph = GraphData()
        self.game_repository = GameRepository()

    def undo(self) -> None:
        """Undo the last human move and subsequent AI moves."""
        if self.rules_engine.current_player_is_human() and self.play_history:
            previous_play = self.play_history.pop()
            self.undo_history.append(previous_play)
            "same for board"
            self.pop_ai_moves_onto(self.play_history, self.undo_history)

    def redo(self) -> None:
        """Redo the last undone human move and subsequent AI moves."""
        if self.rules_engine.current_player_is_human() and self.undo_history:
            last_unplayed_move = self.undo_history.pop()
            self.play_history.append(last_unplayed_move)
            "same for board"
            self.pop_ai_moves_onto(self.undo_history, self.play_history)
            
    def pop_ai_moves_onto(self, source_list: List[Any], target_list: List[Any]) -> None:
        """Move trailing AI moves from source_list onto target_list."""
        while source_list and is_ai_player(source_list[-1]):
            target_list.append(source_list.pop())
            "same for board"

    def print_history(self) -> List[Any]:
        """Return a shallow copy of current play history."""
        return list(self.play_history)

    def clear_undo_history(self) -> None:
        self.undo_history.clear()
    
    def is_undo_history_empty(self) -> bool:
        return len(self.undo_history) == 0
