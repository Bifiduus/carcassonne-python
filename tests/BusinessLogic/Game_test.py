import pytest

from carcassonne.BusinessLogic.Game import Game
from carcassonne.Datas.GraphData import GraphData

<<<<<<< HEAD
<<<<<<< HEAD

class TestGame:
    def test_init_game(self):
        graphData = GraphData()
        game = Game(graphData, 2)
=======
=======
>>>>>>> 8a27fa1 (pytest working thanks to better names for files)
class TestGame:
    def test_init_game(self):
        graphData = GraphData()
        game = Game(graphData)
<<<<<<< HEAD
>>>>>>> 5c81d16 (pytest working thanks to better names for files)
=======
>>>>>>> 8a27fa1 (pytest working thanks to better names for files)
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
<<<<<<< HEAD
<<<<<<< HEAD
        assert game.players is not [], "The game must have a player at start"  # May change

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
        assert len(game.get_history(
        )) is 0, "The undo history must be cleared after starting a new game"
        assert len(
            game.history.future_moves) is 0, "The redo history must be cleared after starting a new game"
        new_graph = game.graph
        assert new_graph.get_verticies(
        )[0] != None, "The vertices of the board must be cleared"
        assert new_graph.get_turn_number() == 1, "The turn number must be re-initialized"
        assert players_order != [], "There must be a players order when you start a new game"
=======
=======
>>>>>>> 8a27fa1 (pytest working thanks to better names for files)
        assert game.players is not [], "The game must have a player at start" # May change
        assert game.players_order == [], "The game instance cannot have an order without a party to play"
    
    def test_start_new_game(self):
        graphData = GraphData()
        game = Game(graphData)
        game.play_move("RRRR/0E1")
        game.play_move("RRFF/1E2")
        graph = game.graph
        players_order = game.players_order
        game.undo()
        game.start_new_game()
        assert game.history.past_moves == [], "The undo history must be cleared after starting a new game"
        assert game.history.future_moves == [], "The redo history must be cleared after starting a new game"
        new_graph = game.graph
        new_players_order = game.players_order
        assert graph.get_verticies() != new_graph.get_verticies(), "The vertices of the board must be cleared"
        assert graph.get_turn_number() != new_graph.get_turn_number() and new_graph.get_turn_number() == 0, "The turn number must be re-initialized"
        assert players_order != new_players_order, "The players order must be different when you start a new game"



<<<<<<< HEAD
>>>>>>> 5c81d16 (pytest working thanks to better names for files)
=======
>>>>>>> 8a27fa1 (pytest working thanks to better names for files)
