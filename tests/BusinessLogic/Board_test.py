import pytest
<<<<<<< HEAD
from carcassonne.BusinessLogic.Board import Board
from carcassonne.Datas.GraphData import GraphData
from carcassonne.Datas.History import History
from carcassonne.Datas.TilesInfo import TilesInfo
from carcassonne.BusinessLogic.Player import Player

<<<<<<< HEAD
<<<<<<< HEAD

=======
>>>>>>> 5c81d16 (pytest working thanks to better names for files)
=======
>>>>>>> 8a27fa1 (pytest working thanks to better names for files)
=======
from carcassonne.business_logic.board import Board
from carcassonne.datas.graph_data import GraphData
from carcassonne.datas.history import History
from carcassonne.datas.tiles_info import TilesInfo
from carcassonne.business_logic.player import Player


>>>>>>> c68e817a063496ba4381991499534e3d7781749c
class TestBoard:
    def test_board_initialization(self):
        board = Board()
        assert board is not None, "Board should be initialized successfully"

    def test_add_tile_to_board(self):
        board = Board()
        graph = GraphData()
        tiles_info = TilesInfo()
        history = History()
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
=======
>>>>>>> c68e817a063496ba4381991499534e3d7781749c
        players: dict[int, Player] = {}
        players[0] = Player(1, "Bob", "blue")
        players[1] = Player(2, "Alice", "red")
        move = "RRRR/1E0"
        board.add_tile_to_board(move, graph, tiles_info,
<<<<<<< HEAD
                                history, players, players[0])
=======
                                history, players, [0, 1], players[0])
>>>>>>> c68e817a063496ba4381991499534e3d7781749c
        assert len(graph.vertices) == 1, "Tile should be added to the graph"
        assert len(
            graph.lands_components) > 0, "Lands components should be updated after adding a tile"
        assert len(
            graph.meeples) == 0, "No meeple should be placed if not specified in the move"

        # Add assertions here to check if the tile was added correctly, lands components were updated, meeples were placed, and the tile was removed from available tiles.
<<<<<<< HEAD
=======
=======
>>>>>>> 8a27fa1 (pytest working thanks to better names for files)
        players = [Player(1,"Bob", "blue"), Player(2,"Alice", "red")]
=======
        players: dict[int, Player] = {}
        players[0] = Player(1,"Bob", "blue")
        players[1] = Player(2,"Alice", "red")
>>>>>>> d609d99 (changes in test, because of new implementations in Game)
        move = "RRRR/1E0"
        board.add_tile_to_board(move, graph, tiles_info, history, players, players[0])
        assert len(graph.vertices) == 1, "Tile should be added to the graph"
        assert len(graph.lands_components) > 0, "Lands components should be updated after adding a tile"
        assert len(graph.meeples) == 0, "No meeple should be placed if not specified in the move"
        
        
<<<<<<< HEAD
        # Add assertions here to check if the tile was added correctly, lands components were updated, meeples were placed, and the tile was removed from available tiles.
>>>>>>> 5c81d16 (pytest working thanks to better names for files)
=======
        # Add assertions here to check if the tile was added correctly, lands components were updated, meeples were placed, and the tile was removed from available tiles.
>>>>>>> 8a27fa1 (pytest working thanks to better names for files)
=======
>>>>>>> c68e817a063496ba4381991499534e3d7781749c
