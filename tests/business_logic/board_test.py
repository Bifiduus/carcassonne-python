import pytest
from carcassonne.business_logic.board import Board
from carcassonne.datas.graph_data import GraphData
from carcassonne.datas.history import History
from carcassonne.datas.tiles_info import TilesInfo
from carcassonne.business_logic.player import Player


class TestBoard:
    def test_board_initialization(self):
        board = Board()
        assert board is not None, "Board should be initialized successfully"

    def test_add_tile_to_board(self):
        board = Board()
        graph = GraphData()
        tiles_info = TilesInfo()
        history = History()
        players: dict[int, Player] = {}
        players[0] = Player(1, "Bob", "blue")
        players[1] = Player(2, "Alice", "red")
        move = "RRRR/1E0"
        board.add_tile_to_board(move, graph, tiles_info,
                                history, players, [0, 1], players[0])
        assert len(graph.vertices) == 1, "Tile should be added to the graph"
        assert len(
            graph.lands_components) > 0, "Lands components should be updated after adding a tile"
        assert len(
            graph.meeples) == 0, "No meeple should be placed if not specified in the move"

        # Add assertions here to check if the tile was added correctly, lands components were updated, meeples were placed, and the tile was removed from available tiles.
