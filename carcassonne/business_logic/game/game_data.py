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
        self.seed = None
        self.maximum_number_of_players = 5
        self.minimum_number_of_players = 2
        self.number_of_ai_players = 0
        self.default_seed = None
        self.shuffle_algo = "fisher-yates"
        self.current_hand = None
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
        self.blitz_manager = BlitzManager()
        self._end_game_scored = False
        # self._initialize_blitz_state()
        self.reset()

    def reset(self):
        """Reset all game data to start a new game."""
        self.graph.reset_graph()
        self.board = Board()
        self.tiles_info = TilesInfo()
        self.rules_manager = RulesManager(self.tiles_info)
        self.current_hand = None

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

    def play_ai_turn(self) -> None:
        from .ai_model import RandomPlayer
        from .ai_model import ExpectimaxPlayer
        from .ai_model import MCTSPlayer

        self.tick_blitz()
        if not self._ensure_current_player_playable():
            return
        if not self.get_current_player().is_ai_player():
            return

        ai_player = self.get_current_player()
        print(f"AI Player {ai_player.get_username()} is thinking...")
        self.draw_tile()
        if self.current_hand is None:
            return
        ai_time = self.get_game_configuration().get("ai_time")
        model = None
        move = None
        eval_score = None
        if self.get_game_configuration().get("ai_mode") == "random":
            model = RandomPlayer()
            move = model.random_move(self.current_hand, self)
        elif self.get_game_configuration().get("ai_mode") == "minimax":
            start_time = time.time()
            depth = self.get_game_configuration().get("ai_minimax_depth")
            model = ExpectimaxPlayer(self, start_time, ai_time, depth)
            eval_score, move = model.search(
                self,
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
            model = MCTSPlayer(self, start_time, ai_time, eval_fn_name)
            move = model.mcts(self)
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
