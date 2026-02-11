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
        self.default_seed = None
        self.shuffle_algo = "fisher-yates"

    def start_new_game(self) -> None:
        """Start a new game by clearing the play history, undo history, 
        and resetting the graph and game repository.
        """
        self.history.clear_history()
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

    def rotate_dirs(self, dirs, rotation):
        rotation = rotation % 4
        return dirs[-rotation:] + dirs[:-rotation]

    def generate_tile_ascii(self, vertex):
        dirs = list(vertex.get_name())  # [N, E, S, W]
        rotation = self.graph.get_vertex_orientation(vertex.get_id())  # 0 à 3

        n, e, s, w = self.rotate_dirs(dirs, rotation)
        m = "{:^3}".format(vertex.get_id())
        if vertex.get_middle() != "":
            m = "{:^5}".format("[" + str(vertex.get_id()) + "/" + vertex.get_middle() + "]")
        else : 
            m = "{:^5}".format("[" + str(vertex.get_id()) + "]")
        space=3*" "

        return [
            space +"{:^5}".format(n) + space,
            "{:^3}".format(w) +"{:^5}".format(m) + "{:^3}".format(e),
            space + "{:^5}".format(s) + space,
        ]

    def get_board(self):
        vertices = list(self.graph.get_verticies().values())

        if not vertices:
            print("No vertices.")
            return

        positions = [v.get_position() for v in vertices]

        min_x = min(x for x, y in positions)
        min_y = min(y for x, y in positions)
        max_x = max(x for x, y in positions)
        max_y = max(y for x, y in positions)

        width = max_x - min_x + 1
        height = max_y - min_y + 1

        board = [[None for _ in range(width)]
                        for _ in range(height)]

        for v in vertices:
            x, y = v.get_position()
            nx = x - min_x
            ny = y - min_y
            board[ny][nx] = self.generate_tile_ascii(v)

        self.print_board(board)

    def print_board(self, board):
        TILE_HEIGHT = 3
        EMPTY_TILE = [" " * 9] * TILE_HEIGHT

        for row in board:               # chaque ligne de tuiles
            for i in range(TILE_HEIGHT):  # chaque ligne ASCII interne
                line = []
                for tile in row:
                    if tile is None:
                        line.append(EMPTY_TILE[i])
                    else:
                        line.append(tile[i])
                print("   ".join(line))
            print()  # espace entre lignes de tuiles
    
    def shuffle_deck(self, algo=None, seed=None):
        if algo is None:
            algo = self.shuffle_algo
        if seed is None:
            if self.default_seed is not None:
                seed = self.default_seed
            else:
                seed = Seed().seed
        if algo == "naive":
            self.deck.shuffle_naive(seed)
        else:
            self.deck.shuffle_fisher_yates(seed)
        self.seed = seed
        return seed
    
    def saveGameToFile(self, filename: str) -> None:
        file = open(filename, 'w')
        file.write("[Settings]\n")

        file.write("\n")
        file.write("[GameState]\n")
        ## + who is the current player, scores, etc.
        file.write(str(self.get_game_configuration()))
        file.write("\n")
        file.write("[History]\n")
        moves_history = self.history.past_moves.copy()
        while moves_history:
            move = moves_history.pop()
            file.write(move.move_str + "\n")
        file.write("\n")

    def loadGameFromFile(self, filename: str) -> None:
        file = open(filename, 'r')
        lines = file.readlines()
        settings_section = False
        game_state_section = False
        history_section = False
        for line in lines:
            line = line.strip()
            if line == "[Settings]":
                settings_section = True
                game_state_section = False
                history_section = False
                continue
            elif line == "[GameState]":
                settings_section = False
                game_state_section = True
                history_section = False
                continue
            elif line == "[History]":
                settings_section = False
                game_state_section = False
                history_section = True
                continue
            elif line == "":
                continue  # Skip empty lines
            
            if settings_section:
                # Here you would parse the settings and set up the game accordingly.
                # This is a placeholder for demonstration purposes.
                print("Parsing settings: ", line)
            elif game_state_section:
                # Here you would parse the game state and set up the board and graph accordingly.
                # This is a placeholder for demonstration purposes.
                print("Parsing game state: ", line)
            elif history_section:
                self.play_move(line.split(':')[1])  # Assuming line is in the format "player_id:details"

        
