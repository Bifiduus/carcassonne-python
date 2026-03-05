import pytest

from carcassonne.BusinessLogic.Game import Game
from carcassonne.Datas.GraphData import GraphData

class TestGame:
    def test_init_game(self):
        graphData = GraphData()
        game = Game(graphData, 2)
        assert game.game_configuration is not None, "The game must have a configuration"
        assert game.game_repository is not None, "The game muste have a repository"
        assert game.graph is not None, "The game must have a graph"
        assert game.tiles_info is not None, "The game must have the tiles' informations"
        assert game.rules_manager is not None, "The game must have a rules_manager"
        assert game.history is not None, "The game must have an instance of the history class"
        assert game.board is not None, "The game muste have an instance of the board class"
        assert game.deck is not None, "The game must have a deck of tiles"
        assert game.seed is None, "The game must not have a seed right after initialisation"
        assert game.shuffle_algo == "fisher-yates", "The shuffle algorithm at start must be the fisher-yates version"
        assert game.current_hand is None, "The game cannot have a current game at initialisation"
        assert game.players is not [], "The game must have a player at start" # May change
    
    def test_start_new_game(self):
        graphData = GraphData()
        game = Game(graphData, 1)
        game.draw_tile()
        game.play_move("RRRR/0E1")
        game.draw_tile()
        game.play_move("CRRR/1E2")
        graph = game.graph
        players_order = game.players_order
        game.start_new_game()
        assert len(game.get_history()) is 0, "The undo history must be cleared after starting a new game"
        assert len(game.history.future_moves) is 0, "The redo history must be cleared after starting a new game"
        new_graph = game.graph
        assert new_graph.get_verticies()[0] != None, "The vertices of the board must be cleared"
        assert new_graph.get_turn_number() == 1, "The turn number must be re-initialized"
        assert players_order != [], "There must be a players order when you start a new game"



