from carcassonne.business_logic.game.game_data import GameData
from carcassonne.presentation.interfaces.i_game_service import IGameService


class NewGame():
    def __init__(self, game_data: GameData):
        self.game_data = game_data

    def start_online_game(self, players: list[Player]):
        if len(players) > self.get_maximum_number_of_players():
            return "Error, too many players: Maximum players" \
                f" is {self.get_maximum_number_of_players()}"
        self.history.clear_history()
        self.graph.reset_graph()
        self.current_hand = None
        self.board = Board()
        self.deck = Deck()
        self.tiles_info = TilesInfo()
        self.rules_manager = RulesManager(self.tiles_info)
        self.players.clear()
        self.add_online_players(players)
        self.shuffle_deck()
        self.shuffle_players_order()
        self.current_player_order_list = 0
        return "Starting the game."

    def start_new_game(self, players_order: list[int] | None = None,
                       seed: int | None = None) -> None:
        """Start a new game by clearing the play history, undo history,
        and resetting the graph and game repository.
        """
        self.history.clear_history()
        self.graph.reset_graph()
        self.board = Board()
        self.deck = Deck()
        self.current_hand = None
        self.tiles_info = TilesInfo()
        self.rules_manager = RulesManager(self.tiles_info)
        if players_order is not None:
            self.players_order = players_order
        else:
            self.shuffle_players_order()
        self.shuffle_deck(None, seed)
        self.current_player_order_list = 0
        self._end_game_scored = False
        self._initialize_blitz_state()
        while self.get_current_player().is_ai_player():
            if self.end_game():
                break
            previous_player_id = self.get_current_player().get_id()
            self.play_ai_turn()
            if self.end_game():
                break
            if self.get_current_player().get_id() == previous_player_id:
                break
