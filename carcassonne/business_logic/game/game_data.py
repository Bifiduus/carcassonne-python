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
        self.save_handler = SaveHandler(self)
        self.score_manager = ScoreManager()
        self.error_message = ""
        self.blitz_manager = BlitzManager(self)
        self.deck_manager = DeckManager(self)
        self._end_game_scored = False
        self._initialize_blitz_state()
        self.reset()

    def reset(self):
        """Reset all game data to start a new game."""
        self.graph.reset_graph()
        self.board = Board()
        self.tiles_info = TilesInfo()
        self.rules_manager = RulesManager(self.tiles_info)
        self.current_hand = None
        self.history = History()

    def start_load_game(self):
        self.history.clear_history()
        self.graph.reset_graph()
        self.game_repository = GameRepository()
        self.board = Board()
        self.deck = Deck()
        self.current_hand = None
        self.tiles_info = TilesInfo()
        self.rules_manager = RulesManager(self.tiles_info)
        self.current_player_order_list = 0
        self._end_game_scored = False
        self._initialize_blitz_state()

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

    def tick_blitz(self) -> bool:
        """Tick the blitz timer and return True if timeout occurred."""
        if self.blitz_manager is None:
            return False
        return self.blitz_manager.tick_blitz()

    def _ensure_current_player_playable(self) -> bool:
        """Ensure the current player is playable (not timed out)."""
        if self.blitz_manager is None:
            return True
        if not self.blitz_manager._has_playable_player():
            return False
        return self.blitz_manager._advance_to_next_playable_player()

    def _initialize_blitz_state(self) -> None:
        """Initialize the blitz state."""
        if self.blitz_manager is not None:
            self.blitz_manager._initialize_blitz_state()

    def play_move(self, move: str) -> bool:
        """
        Tries to place a tile according to the computed move :
        - Checks if the move is a string.
        - Splits the move into parts.
        - Validates each part of the move.
        - Tests if the move is legal in the current game state.
        - If all checks pass, places the tile in the game structures.
        """
        timed_out_now = self.tick_blitz()
        if timed_out_now:
            return False
        if not self._ensure_current_player_playable():
            return False

        if (
            self.players_order[self.current_player_order_list]
            != self.get_current_player().get_id()
        ):
            print("It is not your turn to play.")
            expected_player = self.players_order[
                self.current_player_order_list
            ]
            print(
                "The one: "
                f"{expected_player} {self.current_player_order_list}. "
                f"You: {self.get_current_player()}"
            )
            turn = max(self.graph.get_verticies().keys(), default=-1) + 1
            print(f"turn:{turn}")
            print(self.players_order)
            return False
        if self.current_hand is None:
            print("Vous devez piocher une tuile avant de jouer.")
            return False

        tile_code = self.extract_tile_code(move)
        if tile_code is not None and tile_code != self.current_hand:
            print(f"Vous devez jouer la tuile en main: {self.current_hand}")
            return False

        try:
            parsed_move = parse_move(move)
        except ValueError:
            return False
        current_player_meeples = self.get_current_player().get_meeples()
        if parsed_move.get("meeple") and current_player_meeples <= 0:
            print("No meeple remaining")
            return False

        ok = self.rules_manager.check_move(
            move,
            self.graph,
            current_player_id=self.get_current_player().get_id(),
        )
        if ok:
            current_player = self.get_current_player()
            self.board.add_tile_to_board(
                move,
                self.graph,
                self.tiles_info,
                self.history,
                self.players,
                self.players_order,
                current_player,
            )
            print(move + " placed successfully.")
            self.current_hand = None
            self.current_player_order_list = (
                self.current_player_order_list + 1
            ) % self.get_number_of_players()
            self._ensure_current_player_playable()
            """vertices = self.graph.get_verticies()
            for vertex in vertices.values():
                print(vertex.get_neighbors())"""
            return True
        """vertices = self.graph.get_verticies()
        for vertex in vertices.values():
            print(vertex.get_neighbors())
        print('i failed the test')"""
        return False

    def play_ai_turn(self, game=None) -> None:
        from carcassonne.business_logic.ai_model import RandomPlayer
        from carcassonne.business_logic.ai_model import ExpectimaxPlayer
        from carcassonne.business_logic.ai_model import MCTSPlayer

        if game is None:
            raise ValueError("game parameter is required for play_ai_turn")

        self.tick_blitz()
        if not self._ensure_current_player_playable():
            return
        if not self.get_current_player().is_ai_player():
            return

        ai_player = self.get_current_player()
        print(f"AI Player {ai_player.get_username()} is thinking...")
        self.deck_manager.draw_tile()
        if self.current_hand is None:
            return
        ai_time = self.get_game_configuration().get("ai_time")
        model = None
        move = None
        eval_score = None
        if self.get_game_configuration().get("ai_mode") == "random":
            model = RandomPlayer()
            move = model.random_move(self.current_hand, game)
        elif self.get_game_configuration().get("ai_mode") == "minimax":
            start_time = time.time()
            depth = self.get_game_configuration().get("ai_minimax_depth")
            model = ExpectimaxPlayer(game, start_time, ai_time, depth)
            eval_score, move = model.search(
                game,
                depth=model.depth_max,
                alpha=float("-inf"),
                beta=float("inf"),
                player_to_max=ai_player.get_id(),
                next_player=ai_player.get_id(),
            )
        elif self.get_game_configuration().get("ai_mode") == "mcts":
            start_time = time.time()
            eval_fn_name = self.get_game_configuration().get(
                "ai_mcts_selection"
            )
            model = MCTSPlayer(game, start_time, ai_time, eval_fn_name)
            move = model.mcts(game)
        if not move:
            print(
                f"AI Player {ai_player.get_username()} has no legal move."
            )
            return
        if eval_score is None:
            print(
                f"AI Player {ai_player.get_username()} chooses move: {move}"
            )
        else:
            print(
                f"AI Player {ai_player.get_username()} chooses move: {move} "
                f"with evaluation score: {eval_score}"
            )
        # print("main avant de jouer le coup" + self.current_hand)
        move_played = self.play_move(move)
        if not move_played:
            fallback_played = False
            try:
                parsed = parse_move(move)
            except ValueError:
                parsed = {}

            # AI can still produce meeple moves from simulations where stock
            # differs from the live state. Retry once without meeple.
            if parsed.get("meeple") and ai_player.get_meeples() <= 0:
                fallback_move = move.rsplit("/", 1)[0]
                print(
                    "AI move rejected (no meeples left). "
                    f"Retrying without meeple: {fallback_move}"
                )
                fallback_played = self.play_move(fallback_move)

            if not fallback_played:
                print(
                    f"AI Player {ai_player.get_username()} produced an "
                    "invalid move."
                )
                return
