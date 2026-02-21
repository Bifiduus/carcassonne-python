"""This module defines the Game class, which implements the IGameService interface. 
The Game class is responsible for managing the game state, including the play history and undo history. It interacts with the RulesEngine to determine if the current player is human and with the GameRepository to store and retrieve game data.
"""
from typing import Any, List

from carcassonne.Datas.Deck import Deck
from carcassonne.Datas.Seed import Seed
from carcassonne.Datas.Serializer import parse_move, build_str
from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData
from carcassonne.BusinessLogic.Player import Player
from carcassonne.BusinessLogic.RulesManager import RulesManager
from carcassonne.BusinessLogic.Board import Board
from carcassonne.Datas.GameRepository import GameRepository
from carcassonne.Presentation.Interfaces.IGameService import IGameService
from carcassonne.Datas.History import History, MoveRecord 
from carcassonne.BusinessLogic.Interfaces.ITilesInfo import ITilesInfo
from carcassonne.Datas.TilesInfo import TilesInfo
from .AIModel import is_ai_player

OPPOSITE = {
    "N": "S",
    "S": "N",
    "E": "W",
    "W": "E"
}

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
        self.current_hand = None
        self.save_file = None
        self.players : list[Player] = []
        self.players : list[Player] = []
        self.players_order: list[int] = []

    def start_new_game(self) -> None:
        """Start a new game by clearing the play history, undo history, 
        and resetting the graph and game repository.
        """
        self.history.clear_history()
        self.graph.reset_graph()
        self.game_repository = GameRepository()
        self.board = Board()
        self.deck = Deck()
        self.current_hand = None
        self.seed = None
        self.tiles_info= TilesInfo()
        self.rules_manager = RulesManager(self.tiles_info)

    def undo(self) -> None:
        """Undo the last human move and subsequent AI moves."""
        if self.rules_manager.current_player_is_human() and self.history.past_moves:
            previous_play = self.history.pop_past()
            self.history.push_future(previous_play)
            self.board.remove_tile_from_board(build_str(previous_play), self.graph, self.tiles_info, self.history)
            while self.history.past_moves and is_ai_player(self.history.past_moves[-1]):
                self.board.remove_tile_from_board(build_str(self.history.past_moves[-1]), self.graph, self.tiles_info, self.history)
                self.history.push_future(self.history.pop_past())

    def redo(self) -> None:
        """Redo the last undone human move and subsequent AI moves."""
        if self.rules_manager.current_player_is_human() and self.history.future_moves:
            last_unplayed_move = self.history.pop_future()
            self.current_hand = last_unplayed_move.move_str.split('/')[0]
            self.play_move(last_unplayed_move.move_str) 
            while self.history.future_moves and is_ai_player(self.history.future_moves[-1]):
                self.play_move(self.history.future_moves[-1].move_str) 
                self.history.push_past(self.history.pop_future())

    def get_history(self) -> List[str]:
        """Return the current play history."""
        return self.history.list_history()

    def clear_undo_history(self) -> None:
        self.history.clear_future()
    
    def is_undo_history_empty(self) -> bool:
        return len(self.history.future_moves) == 0


    def play_move(self, move) -> None:
        """
        Tries to place a tile according to the computed move :
        - Checks if the move is a string.
        - Splits the move into parts.
        - Validates each part of the move.
        - Tests if the move is legal in the current game state.
        - If all checks pass, places the tile in the game structures.
        """
        if self.current_hand is None:
            print("Vous devez piocher une tuile avant de jouer.")
            return

        tile_code = self.extract_tile_code(move)
        if tile_code is not None and tile_code != self.current_hand:
            print(f"Vous devez jouer la tuile en main: {self.current_hand}")
            return

        ok = self.rules_manager.check_move(move, self.graph)
        if ok:
            self.board.add_tile_to_board(move, self.graph, self.tiles_info, self.history, self.players)   
            print(move + " placed successfully.")
            self.current_hand = None
        
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

    def draw_tile(self) -> str | None:
        if self.current_hand is not None:
            return self.current_hand

        tile = self.deck.draw()
        if tile is None:
            return None
        self.current_hand = tile
        return tile
    
    def maximum_number_of_players(self) -> int:
        return 5
    
    def minimum_number_of_players(self) -> int:
        return 2
    
    def set_number_of_ai_players(self, num_players: int) -> None:
        self.number_of_ai_players = num_players

    def get_current_player(self) -> int:
        return self.players_order[(self.graph.get_turn_number()-1) % len(self.players)]
    
    def save_game_to_file(self, filename: str) -> int:
        if filename is None or filename.strip() == "":
            print("Error: Invalid filename.")
            return -1
        if not filename.endswith(".txt"):
            filename += ".txt"
        file = open(filename, 'w')

        file.write("[Settings]\n")
        file.write(str(self.get_game_configuration()) + "\n")

        file.write("\n")
        file.write("[GameState]\n")
        ## + who is the current player, scores, etc.
        file.write("NumberOfPlayers: " + str(len(self.players)) + ", 0\n") # str(self.game_repository.get_number_of_ai_players()) 
        file.write("PlayersOrder: " + str(self.players_order) + "\n")
        file.write("GameScore: [" + ", ".join([f"{player.get_id()}: {player.get_score().score}" for player in self.players]) + "]\n")
        file.write("\n")
        file.write("[History]\n")
        moves_history = self.get_history()
        while moves_history:
            move = moves_history.pop()
            file.write(move + "\n")
        file.write("\n")
        return 0

    def load_game_from_file(self, filename: str) -> int:
        if filename is None or filename.strip() == "":
            print("Error: Invalid filename.")
            return -1
        try:
            file = open(filename, 'r')
        except OSError:
            print(f"Error: Could not open file {filename}")
            return -1
        self.start_new_game()  # Clear current game state before loading new one

        lines = file.readlines()
        settings_section = False
        game_state_section = False
        history_section = False
        commentary = False
        settings_parsed = False
        game_state_parsed = False
        history_parsed = False
        commentary = False
        sections_parsed = 0
        for line in lines:
            # Remove comments and strip whitespace
            line = line.strip().split("#")[0]

            # Handle cases where comments are inline with data
            if line.find("{") != -1 and line.find("}") == -1:
                line1 = line.split("{")[0]
                line2 = line.split("{")[1] 
                line = line1 + line2

            if line.find("{") != -1:
                line = line.split("{")[0]
                commentary = True
                continue
            if line.find("}") != -1:
                line = line.split("}")[1]
                commentary = False
            if commentary:
                continue

            if line == "[Settings]":
                sections_parsed += 1
                settings_section = True
                game_state_section = False
                history_section = False
                settings_parsed = True
                continue
            elif line == "[GameState]":
                if not settings_section:
                    print("Warning: [Settings] section not found before [GameState].")
                sections_parsed += 1
                settings_section = False
                game_state_section = True
                history_section = False
                game_state_parsed = True
                continue
            elif line == "[History]":
                if not game_state_section:
                    print("Warning: [GameState] section not found before [History].")
                sections_parsed += 1
                settings_section = False
                game_state_section = False
                history_section = True
                history_parsed = True
                continue
            elif line == "":
                continue  # Skip empty lines
            
            if settings_section:
                # Here you would parse the settings and set up the game accordingly.
                # This is a placeholder for demonstration purposes.
                # Configuration of the game, shuffle algorithm and seed.
                print("Parsing settings: ", line)
            elif game_state_section:
                # Here you would parse the game state.
                # This is a placeholder for demonstration purposes.
                # Game scores and player order.
                print("Parsing game state: ", line)

                if line.startswith("NumberOfPlayers:"):
                    line = line.split("NumberOfPlayers:")[1].strip()
                    if line == "":
                        print("Warning: Number of players not specified.")
                        continue
                    number_of_players, number_of_ai_players = line.split(",") if "," in line else (line, "0")
                    print(f"Total number of players specified: {int(number_of_ai_players.strip()) + int(number_of_players.strip())}.")
                    if int(number_of_ai_players.strip()) + int(number_of_players.strip()) > self.maximum_number_of_players():
                        print(f"Warning: Number of players should be between {self.minimum_number_of_players()} and {self.maximum_number_of_players()}.")
                        continue
                    self.set_number_of_ai_players(int(number_of_ai_players.strip()))
                    print(f"Number of players set to {int(number_of_players.strip()) + int(number_of_ai_players.strip())}.")

                if line.startswith("PlayersOrder:"):
                    line = line.split("PlayersOrder:")[1].strip()
                    if line == "":
                        print("Warning: Players order not specified.")
                        continue
                    self.players_order = [int(player_id.strip()) for player_id in line.strip("[]").split(",")]
                    print(f"Players order set to {self.players_order}.")

                game_score = False
                if line.startswith("GameScore:"):
                    line = line.split("GameScore:")[1].strip() # Assuming the format is "GameScore: [Player1ID: 10, Player2ID: 20]"
                    if line == "" or line == "[]":
                        print("Warning: No score yet.")
                        continue
                    line = line.split("[")[1].strip("]")
                    scores = line.split(",")
                    if len(scores) > len(self.players):
                        print("Warning: More scores than players.")
                    for score in scores:       
                        playerID, points = score.split(":")
                        for player in self.players:
                            if player.get_id() == int(playerID.strip()):
                                player.score.setPoints(int(points.strip()))
                                print(f"Player number {self.players_order.index(player.get_id())} ({player.get_username().strip()}) has {player.score.score} points.")
                        game_score = True
                if not game_score:
                    print("Warning: no game score found in [GameState] section.")
            elif history_section:
                move = line.split(':')[1]
                print("Playing move from history: ", move)
                self.current_hand = move
                self.play_move(move)  # Assuming line is in the format "player_id:details"
        if sections_parsed < 3:
            print("Warning: Not all sections were found in the file.")
            if not settings_parsed:
                print("Warning: [Settings] section missing.")
            if not game_state_parsed:
                print("Warning: [GameState] section missing.")
            if not history_parsed:
                print("Warning: [History] section missing.")
        return 0       


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
        return vertices
    
    def get_board_data(self) -> list[dict]:
        """
        Retourne une liste exploitable directement par la GUI.
        """
        vertices = self.graph.get_vertices_data()

        return list(vertices.values())

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

    def get_close_neighbors(self, x: int, y: int) -> tuple[int | None, int | None]:
        return self.graph.find_neighbor_at(x, y)
    
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

    def extract_tile_code(self, move):
        try:
            parsed = parse_move(move)
        except ValueError:
            return None

        tile_code = parsed["tile_sides"]
        if parsed.get("center"):
            tile_code = f"{tile_code}/{parsed['center']}"
        return tile_code