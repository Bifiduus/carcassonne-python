"""This module defines the Game class, which implements the IGameService interface. 
The Game class is responsible for managing the game state, including the play history and undo history. It interacts with the RulesEngine to determine if the current player is human and with the GameRepository to store and retrieve game data.
"""
from typing import Any, List

from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData
from carcassonne.BusinessLogic.RulesManager import RulesManager
from carcassonne.Datas.GameRepository import GameRepository
from carcassonne.Datas.GraphData import GraphData
from carcassonne.Presentation.Interfaces.IGameService import IGameService
from carcassonne.Datas.History import History  
from .AIModel import is_ai_player

class Game(IGameService):

    def __init__(self, graphData: IGraphData) -> None:
    
        self.game_repository: GameRepository = GameRepository()
        self.graph: IGraphData = graphData
        self.rules_engine: RulesManager = RulesManager(self)
        self.history: History = History()

    def start_new_game(self) -> None:
        """Start a new game by clearing the play history, undo history, 
        and resetting the graph and game repository.
        """
        self.history.clear_future()
        self.graph.reset_graph()
        self.game_repository = GameRepository()

    def undo(self) -> None:
        """Undo the last human move and subsequent AI moves."""
        if self.rules_engine.current_player_is_human() and self.history.past_moves:
            previous_play = self.history.pop_past()
            self.history.push_future(previous_play)
            while self.history.past_moves and is_ai_player(self.history.past_moves[-1]):
                self.history.push_future(self.history.pop_past())

    def redo(self) -> None:
        """Redo the last undone human move and subsequent AI moves."""
        if self.rules_engine.current_player_is_human() and self.history.future_moves:
            last_unplayed_move = self.history.pop_future()
            self.history.push_past(last_unplayed_move)
            while self.history.future_moves and is_ai_player(self.history.future_moves[-1]):
                self.history.push_past(self.history.pop_future())

    def print_history(self) -> List[Any]:
        """Return a shallow copy of current play history."""
        return list(self.history.past_moves)

    def clear_undo_history(self) -> None:
        self.history.clear_future()
    
    def is_undo_history_empty(self) -> bool:
        return len(self.history.future_moves) == 0



    def play_move(self, move):
        self.history.push_past(move)


    def get_game_configuration(self) -> dict :
        grid = {}
        for vertex in self.graph.get_verticies().values():
            pos = vertex.get_position()
            grid[pos] = {
                "name": vertex.get_name(),
                "orientation": vertex.get_orientation(),
                "neighbors": vertex.get_neighbors()
            }
        return grid