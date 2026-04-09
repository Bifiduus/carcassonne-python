from carcassonne.business_logic.game.game_data import GameData
from carcassonne.interfaces.i_business_logic_factory import (
    IBusinessLogicFactory,
)
from carcassonne.interfaces.i_datas_factory import IDatasFactory
from carcassonne.business_logic.player import Player


class NewGame:
    """Orchestrates the initialisation of new and online game sessions.

    Responsible for resetting all game-data structures, setting up the deck
    (including river tiles when enabled), and running any AI opening turns
    before the first human move.
    """

    def __init__(
        self,
        river_manager,
        deck_manager,
        blitz_manager,
        game_data: GameData,
        business_logic_factory: IBusinessLogicFactory,
        datas_factory: IDatasFactory,
        game=None,
    ):
        # Central store of mutable game state shared across all managers.
        self.game_data = game_data
        # Manages river-tile constraints (direction changes, activity flag).
        self.river_manager = river_manager
        # Responsible for drawing and shuffling the tile deck.
        self.deck_manager = deck_manager
        # Handles blitz-mode timers and per-player playability checks.
        self.blitz_manager = blitz_manager
        self.business_logic_factory = business_logic_factory
        self.datas_factory = datas_factory
        # Reference to the Game service; needed to call play_ai_turn.
        self.game = game

    def start_online_game(self, players: list[Player]):
        """Initialise a multiplayer online game with the supplied player list.

        Resets the board, deck and graph, then registers the given players,
        resolves a seed and shuffles the deck and player order.

        Args:
            players: Ordered list of Player objects joining the online game.

        Returns:
            An error string if there are too many players, otherwise a
            confirmation string ``"Starting the game."``.
        """
        if len(players) > self.game_data.get_maximum_number_of_players():
            return (
                "Error, too many players: Maximum players"
                f" is {self.game_data.get_maximum_number_of_players()}"
            )
        self.game_data.history.clear_history()
        self.game_data.graph.reset_graph()
        # ensure starting tile present after reset
        if self.game_data.game_configuration.get_setting_value("river"):
            self.game_data.graph.initialize_starting_tile(river=True)
        else:
            self.game_data.graph.initialize_starting_tile(river=False)
        self.game_data.current_hand = None
        self.game_data.board = self.business_logic_factory.create(
            "Board", self.datas_factory
        )
        self.game_data.deck = self.datas_factory.create("Deck")
        self.game_data.tiles_info = self.datas_factory.create("TilesInfo")
        self.game_data.rules_manager = self.business_logic_factory.create(
            "RulesManager", self.game_data.tiles_info
        )
        self.game_data.players.clear()
        self.game_data.add_online_players(players)
        resolved_seed = self.deck_manager.resolve_seed()
        self.game_data.players_order = list(self.game_data.players.keys())
        self.game_data.shuffle_players_order(resolved_seed)
        self.deck_manager.shuffle_deck(seed=resolved_seed)
        self.game_data.current_player_order_list = 0
        return "Starting the game."

    def start_new_game(
        self, players_order: list[int] | None = None, seed: int | None = None
    ) -> None:
        """Start a new game by clearing the play history, undo history,
        and resetting the graph and game repository.
        """
        self.game_data.history.clear_history()
        self.game_data.graph.reset_graph()
        self.river_manager.reset()
        # ensure starting tile present after reset
        if self.game_data.game_configuration.get_setting_value("river"):
            self.river_manager.initialize_river()
            self.game_data.graph.initialize_starting_tile(river=True)
        else:
            self.game_data.graph.initialize_starting_tile(river=False)
        self.game_data.board = self.business_logic_factory.create(
            "Board", self.datas_factory
        )
        self.game_data.deck = self.datas_factory.create("Deck")
        self.game_data.current_hand = None
        self.game_data.tiles_info = self.datas_factory.create("TilesInfo")
        self.game_data.rules_manager = self.business_logic_factory.create(
            "RulesManager", self.game_data.tiles_info
        )
        resolved_seed = self.deck_manager.resolve_seed(seed)
        if players_order is not None:
            self.game_data.players_order = players_order
        else:
            self.game_data.players_order = list(self.game_data.players.keys())
            self.game_data.shuffle_players_order(resolved_seed)
        for player in self.game_data.players.values():
            player.reset()
        self.deck_manager.shuffle_deck(None, resolved_seed)
        self.game_data.current_player_order_list = 0
        self.game_data._end_game_scored = False
        self.blitz_manager._initialize_blitz_state()
        while self.game_data.get_current_player().is_ai_player():
            end_game = self.business_logic_factory.create(
                "EndGame",
                self.game_data,
                self.blitz_manager,
                self.game_data.rules_manager,
            )
            if end_game.end_game():
                break
            previous_player_id = self.game_data.get_current_player().get_id()
            self.game.play_ai_turn(self.game)
            if end_game.end_game():
                break
            if (self.game_data.get_current_player().get_id()
                    == previous_player_id):
                break
