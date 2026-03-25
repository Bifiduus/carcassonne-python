from carcassonne.business_logic.game.river_manager import RiverManager
from carcassonne.business_logic.score_manager import ScoreManager
from carcassonne.datas.deck import Deck
from carcassonne.datas.seed import Seed
from carcassonne.datas.serializer import parse_move
from carcassonne.business_logic.interfaces.i_graph_data import IGraphData
from carcassonne.business_logic.player import Player
from carcassonne.business_logic.rules_manager import RulesManager
from carcassonne.business_logic.game.board import Board
from carcassonne.datas.games_repository import GameRepository
from carcassonne.datas.game_configuration import GameConfiguration
from carcassonne.presentation.interfaces.i_game_service import IGameService
from carcassonne.datas.history import History
from carcassonne.business_logic.interfaces.i_tiles_info import ITilesInfo
from carcassonne.datas.tiles_info import TilesInfo
from carcassonne.business_logic.save_handler import SaveHandler
from carcassonne.business_logic.game.blitz_manager import BlitzManager
from carcassonne.business_logic.game.deck_manager import DeckManager
from carcassonne.datas.starting_tile import (
    initialize_starting_tile,
    initialize_starting_tile_river,
)
import time
import random as r


class GameData():
    """Class to store all game data, and be able to reset it when needed."""

    def __init__(self, graphData: IGraphData, nb_players: int, config_overrides=None):
        self.game_configuration = GameConfiguration(config_overrides)
        self.game_repository: GameRepository = GameRepository()
        self.graph: IGraphData = graphData
        self.tiles_info: ITilesInfo = TilesInfo()
        self.rules_manager: RulesManager = RulesManager(self.tiles_info)
        self.board: Board = Board()
        self.deck = Deck()
        self.history = History()
        self.seed = None
        self.maximum_number_of_players = 5
        self.minimum_number_of_players = 2
        self.number_of_ai_players = 0
        self.default_seed = None
        self.shuffle_algo = "fisher-yates"
        self.current_hand: str | None = None
        self.save_file = None
        self.players: dict[int, Player] = {}
        self.players[0] = Player(0, "Player 0", "green")
        self.players_order: list[int] = [0]
        self.add_players(nb_players - 1)
        self.shuffle_players_order()
        self.current_player_order_list = 0

        self._end_game_scored = False

    def reset(self):
        """Reset all game data to start a new game."""
        self.graph.reset_graph()
        # Initialize the starting tile on the graph after reset
        if self.game_configuration.get_setting_value("river"):
            initialize_starting_tile_river(self.graph)
        else:
            initialize_starting_tile(self.graph)
        self.board = Board()
        self.tiles_info = TilesInfo()
        self.rules_manager = RulesManager(self.tiles_info)
        self.current_hand = None
        self.history = History()

    def start_load_game(self):
        self.history.clear_history()
        self.graph.reset_graph()
        # ensure starting tile present after reset
        if self.game_configuration.get_setting_value("river"):
            initialize_starting_tile_river(self.graph)
        else:
            initialize_starting_tile(self.graph)
        self.game_repository = GameRepository()
        self.board = Board()
        self.deck = Deck()
        self.current_hand = None
        self.tiles_info = TilesInfo()
        self.rules_manager = RulesManager(self.tiles_info)
        self.current_player_order_list = 0
        self._end_game_scored = False

    def add_players(self, nb_players: int) -> None:
        """Add AI players to the game."""
        colors = ["red", "blue", "yellow", "black", "white"]
        for i in range(1, nb_players + 1):
            self.players[i] = Player(
                i, f"Player {i}", colors[(i - 2) % len(colors)], True
            )
            self.players_order.append(i)
            self.number_of_ai_players += 1

    def add_online_players(self, players: list[Player]) -> None:
        """Add online players to the game."""
        colors = ["red", "blue", "yellow", "black", "white"]
        for i in range(len(players)):
            players[i].set_color(colors[i % len(colors)])
            self.players[i] = players[i]

    def shuffle_players_order(self) -> None:
        """Shuffle the players order."""
        others = [player for player in self.players_order if player != 0]
        r.shuffle(others)
        self.players_order = [0] + others

    def get_current_player(self) -> Player:
        """Get the current player."""
        current_player_id = self.players_order[self.current_player_order_list]
        return self.players[current_player_id]

    def get_number_of_players(self) -> int:
        return len(self.players)

    def get_maximum_number_of_players(self) -> int:
        return self.maximum_number_of_players

    def get_minimum_number_of_players(self) -> int:
        return self.minimum_number_of_players

    def get_game_configuration(self):
        return self.game_configuration.get_setting()

    def extract_tile_code(self, move):
        """Extract the tile code from a move."""
        try:
            parsed = parse_move(move)
        except ValueError:
            return None

        tile_code = parsed["tile_sides"]
        if parsed.get("center"):
            tile_code = f"{tile_code}/{parsed['center']}"
        return tile_code
    
    def is_river_over(self):
        if self.deck.len_river() == 0:
            return True
        return False
