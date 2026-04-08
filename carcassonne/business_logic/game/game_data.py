from carcassonne.business_logic.move_serializer import parse_move
from carcassonne.interfaces.i_business_logic_factory import (
    IBusinessLogicFactory,
)
from carcassonne.interfaces.i_datas_factory import IDatasFactory
from carcassonne.interfaces.i_graph_data import IGraphData
from carcassonne.business_logic.player import Player
from carcassonne.interfaces.i_tiles_info import ITilesInfo
import random as r


class GameData:
    """Class to store all game data, and be able to reset it when needed."""

    def __init__(
        self,
        graphData: IGraphData,
        nb_players: int,
        business_logic_factory: IBusinessLogicFactory,
        datas_factory: IDatasFactory,
        config_overrides=None,
    ):
        self.business_logic_factory = business_logic_factory
        self.datas_factory = datas_factory
        self.game_configuration = self.datas_factory.create(
            "GameConfiguration", config_overrides
        )
        self.game_repository = self.datas_factory.create("GameRepository")
        self.graph: IGraphData = graphData
        self.tiles_info: ITilesInfo = self.datas_factory.create("TilesInfo")
        self.rules_manager = self.business_logic_factory.create(
            "RulesManager", self.tiles_info
        )
        self.board = self.business_logic_factory.create(
            "Board", self.datas_factory
        )
        self.deck = self.datas_factory.create("Deck")
        self.history = self.datas_factory.create("History")
        self.seed = None
        self.maximum_number_of_players = 5
        self.minimum_number_of_players = 2
        self.number_of_ai_players = 0
        self.default_seed = None
        self.shuffle_algo = "fisher-yates"
        self.current_hand: str | None = None
        self.save_file = None
        self.players: dict[int, Player] = {}
        self.players[0] = self.business_logic_factory.create(
            "Player", 0, "Player 0", "green"
        )
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
            self.graph.initialize_starting_tile(river=True)
        else:
            self.graph.initialize_starting_tile(river=False)
        self.board = self.business_logic_factory.create(
            "Board", self.datas_factory
        )
        self.tiles_info = self.datas_factory.create("TilesInfo")
        self.rules_manager = self.business_logic_factory.create(
            "RulesManager", self.tiles_info
        )
        self.current_hand = None
        self.history = self.datas_factory.create("History")
        self._end_game_scored = False

    def start_load_game(self):
        self.history.clear_history()
        self.graph.reset_graph()

        self.game_repository = self.datas_factory.create("GameRepository")
        self.board = self.business_logic_factory.create(
            "Board", self.datas_factory
        )
        self.deck = self.datas_factory.create("Deck")
        self.current_hand = None
        self.tiles_info = self.datas_factory.create("TilesInfo")
        self.rules_manager = self.business_logic_factory.create(
            "RulesManager", self.tiles_info
        )
        self.current_player_order_list = 0
        self._end_game_scored = False

    def initialize_starting_tile_based_on_config(self):
        """Initialize the starting tile based on current game configuration."""
        if self.game_configuration.get_setting_value("river"):
            self.graph.initialize_starting_tile(river=True)
        else:
            self.graph.initialize_starting_tile(river=False)

    def add_players(self, nb_players: int) -> None:
        """Add AI players to the game."""
        colors = ["red", "blue", "yellow", "black", "white"]
        for i in range(1, nb_players + 1):
            self.players[i] = self.business_logic_factory.create(
                "Player",
                i,
                f"Player {i}",
                colors[(i - 2) % len(colors)],
                True,
            )
            self.players_order.append(i)
            self.number_of_ai_players += 1

    def set_number_of_ai_players_configured(self, num_ai: int) -> None:
        """Adjust the number of AI players to match configuration.

        This respects max_players constraint and removes/adds IAs as needed.
        Always keeps player 0 as the human player.

        Args:
            num_ai: Desired number of AI players (1-4).
        """
        # Clamp to valid range
        num_ai = max(1, min(num_ai, self.maximum_number_of_players - 1))
        current_ai_count = len([p for p in self.players if p != 0])

        if current_ai_count == num_ai:
            return  # Already correct

        colors = ["red", "blue", "yellow", "black", "white"]

        if current_ai_count < num_ai:
            # Need to add AI players
            for i in range(current_ai_count + 1, num_ai + 1):
                if i not in self.players:
                    self.players[i] = self.business_logic_factory.create(
                        "Player",
                        i,
                        f"Player {i}",
                        colors[(i - 2) % len(colors)],
                        True,
                    )
                if i not in self.players_order:
                    self.players_order.append(i)
                self.number_of_ai_players = num_ai
        else:
            # Need to remove AI players
            players_to_remove = []
            for i in range(num_ai + 1, current_ai_count + 1):
                if i in self.players:
                    players_to_remove.append(i)
            for i in players_to_remove:
                del self.players[i]
                if i in self.players_order:
                    self.players_order.remove(i)
            self.number_of_ai_players = num_ai

    def add_online_players(self, players: list[Player]) -> None:
        """Add online players to the game."""
        colors = ["red", "blue", "yellow", "black", "white"]
        self.players.clear()
        self.players_order.clear()
        for i in range(len(players)):
            players[i].set_color(colors[i % len(colors)])
            self.players[i + 1] = players[i]
            self.players_order.append(players[i].get_id())

    def shuffle_players_order(self, seed: int | None = None) -> None:
        """Shuffle the players order."""
        others = [player for player in self.players_order]
        if seed is None:
            r.shuffle(others)
        else:
            rng = r.Random(seed)
            rng.shuffle(others)
        self.players_order = others

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
        hand = ""
        if self.current_hand is not None:
            hand = self.current_hand
        if self.deck.len_river() == 0 and "S" not in [str for str in hand]:
            return True
        return False
