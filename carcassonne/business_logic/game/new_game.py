from carcassonne.business_logic.game.game_data import GameData
from carcassonne.business_logic.player import Player
from carcassonne.business_logic.game.board import Board
from carcassonne.datas.deck import Deck
from carcassonne.datas.tiles_info import TilesInfo
from carcassonne.business_logic.rules_manager import RulesManager
from carcassonne.datas.starting_tile import (
    initialize_starting_tile,
    initialize_starting_tile_river,
)


class NewGame():
    def __init__(self, river_manager, deck_manager, blitz_manager,
                 game_data: GameData, game=None):
        self.game_data = game_data
        self.river_manager = river_manager
        self.deck_manager = deck_manager
        self.blitz_manager = blitz_manager
        self.game = game

    def start_online_game(self, players: list[Player]):
        if len(players) > self.game_data.get_maximum_number_of_players():
            return "Error, too many players: Maximum players" \
                f" is {self.game_data.get_maximum_number_of_players()}"
        self.game_data.history.clear_history()
        self.game_data.graph.reset_graph()
        # ensure starting tile present after reset
        if self.game_data.game_configuration.get_setting_value("river"):
            initialize_starting_tile_river(self.game_data.graph)
        else:
            initialize_starting_tile(self.game_data.graph)
        self.game_data.current_hand = None
        self.game_data.board = Board()
        self.game_data.deck = Deck()
        self.game_data.tiles_info = TilesInfo()
        self.game_data.rules_manager = RulesManager(self.game_data.tiles_info)
        self.game_data.players.clear()
        self.game_data.add_online_players(players)
        self.deck_manager.shuffle_deck()
        self.game_data.shuffle_players_order()
        self.game_data.current_player_order_list = 0
        return "Starting the game."

    def start_new_game(self, players_order: list[int] | None = None,
                       seed: int | None = None) -> None:
        """Start a new game by clearing the play history, undo history,
        and resetting the graph and game repository.
        """
        self.game_data.history.clear_history()
        self.game_data.graph.reset_graph()
        # ensure starting tile present after reset
        if self.game_data.game_configuration.get_setting_value("river"):
            self.river_manager.initialize_river()
            initialize_starting_tile_river(self.game_data.graph)
        else:
            initialize_starting_tile(self.game_data.graph)
        self.game_data.board = Board()
        self.game_data.deck = Deck()
        self.game_data.current_hand = None
        self.game_data.tiles_info = TilesInfo()
        self.game_data.rules_manager = RulesManager(self.game_data.tiles_info)
        if players_order is not None:
            self.game_data.players_order = players_order
        else:
            self.game_data.shuffle_players_order()
        self.deck_manager.shuffle_deck(None, seed)
        self.game_data.current_player_order_list = 0
        self.game_data._end_game_scored = False
        self.blitz_manager._initialize_blitz_state()
        while self.game_data.get_current_player().is_ai_player():
            from .end_game import EndGame
            end_game = EndGame(self.game_data)
            if end_game.end_game():
                break
            previous_player_id = self.game_data.get_current_player().get_id()
            self.game.play_ai_turn(self.game)
            if end_game.end_game():
                break
            if self.game_data.get_current_player().get_id() == previous_player_id:
                break
