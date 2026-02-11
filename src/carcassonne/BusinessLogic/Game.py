"""This module defines the Game class, which implements the IGameService interface. 
The Game class is responsible for managing the game state, including the play history and undo history. It interacts with the RulesEngine to determine if the current player is human and with the GameRepository to store and retrieve game data.
"""
from typing import Any, List

from carcassonne.Datas.Deck import Deck
from carcassonne.Datas.Seed import Seed
from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData
from carcassonne.BusinessLogic.RulesManager import RulesManager
from carcassonne.BusinessLogic.Board import Board
from carcassonne.Datas.GameRepository import GameRepository
from carcassonne.Presentation.Interfaces.IGameService import IGameService
from carcassonne.Datas.History import History, MoveRecord 
from carcassonne.BusinessLogic.Interfaces.ITilesInfo import ITilesInfo
from carcassonne.Datas.TilesInfo import TilesInfo
from .AIModel import is_ai_player

class Game(IGameService):

    def __init__(self, graphData: IGraphData) -> None:
    
        self.game_repository: GameRepository = GameRepository()
        self.graph: IGraphData = graphData
        self.tiles_info: ITilesInfo = TilesInfo()
        self.rules_manager: RulesManager = RulesManager(self.tiles_info)
        self.history: History = History()
        self.board: Board = Board()
        self.deck = Deck()
        self.seed = None

    def start_new_game(self) -> None:
        """Start a new game by clearing the play history, undo history, 
        and resetting the graph and game repository.
        """
        self.history.clear_future()
        self.graph.reset_graph()
        self.game_repository = GameRepository()

    def undo(self) -> None:
        """Undo the last human move and subsequent AI moves."""
        if self.rules_manager.current_player_is_human() and self.history.past_moves:
            previous_play = self.history.pop_past()
            self.history.push_future(previous_play)
            self.board.remove_tile_from_board(previous_play.move_str, self.graph, self.tiles_info, self.history)
            while self.history.past_moves and is_ai_player(self.history.past_moves[-1]):
                self.board.remove_tile_from_board(self.history.past_moves[-1].move_str, self.graph, self.tiles_info, self.history)
                self.history.push_future(self.history.pop_past())

    def redo(self) -> None:
        """Redo the last undone human move and subsequent AI moves."""
        if self.rules_manager.current_player_is_human() and self.history.future_moves:
            last_unplayed_move = self.history.pop_future()
            self.history.push_past(last_unplayed_move)
            self.play_move(last_unplayed_move.move_str.split(':')[1])  # Assuming move_str is in the format "player_id:details"
            while self.history.future_moves and is_ai_player(self.history.future_moves[-1]):
                self.play_move(self.history.future_moves[-1].move_str.split(':')[1])  # Assuming move_str is in the format "player_id:details"
                self.history.push_past(self.history.pop_future())

    def get_history(self) -> List[MoveRecord]:
        """Return a shallow copy of current play history."""
        return self.history.past_moves.copy()

    def clear_undo_history(self) -> None:
        self.history.clear_future()
    
    def is_undo_history_empty(self) -> bool:
        return len(self.history.future_moves) == 0


    def play_move(self, move):
        """
        Tries to place a tile according to the computed move :
        - Checks if the move is a string.
        - Splits the move into parts.
        - Validates each part of the move.
        - Tests if the move is legal in the current game state.
        - If all checks pass, places the tile in the game structures.
        """
        
        ok = self.rules_manager.check_move(move, self.graph)
        if ok:
            self.board.add_tile_to_board(move, self.graph, self.tiles_info, self.history)   
            print(move + " placed successfully.")
        
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
    
    def shuffle_deck(self, algo="fisher-yates", seed=None):
        if seed is None:
            seed = Seed().seed
        if algo == "naive":
            self.deck.shuffle_naive(seed)
        else:
            self.deck.shuffle_fisher_yates(seed)
        self.seed = seed
        return seed