import pytest

from carcassonne.datas.graph_data import Vertex, GraphData
from carcassonne.datas.meeple_data import Meeple


class TestGraphData:

    def test_graph_creation(self):
        graph = GraphData()
        assert graph is not None, "GraphData instance should be created successfully"
        assert graph.turn == 1, "Initial turn should be 1"
        assert len(
            graph.vertices) == 1, "Initial vertices dict should have one vertex"
        assert graph.lands_components != {}, "Initial lands components dict should not be empty"
        assert graph.next_set_id != {}, "Initial next set ID dict should not be empty"
        assert graph.meeples == [], "Initial meeples list should be empty"
        assert graph.vertices[0] != None, "Vertex with ID 0 should exist in the graph"

    def test_graph_add_vertex(self):
        graph = GraphData()
        turn = graph.turn
        vertex = Vertex(id=1, name="RRRR", middle="",
                        tile_dict=graph.tiles_dict["RRRR"].tiles_lands, orientation=0, position=(0, 1))
        graph.add_vertex(vertex_id=vertex.id, name=vertex.name, middle=vertex.middle,
                         orientation=vertex.orientation, position=vertex.position)
        assert "RRRR" in [v.name for v in graph.vertices.values(
        )], "Vertex 'RRRR' should be added to the graph"
        assert graph.turn == turn + 1, "Turn should be incremented after adding a vertex"
        assert graph.vertices[1].id == vertex.id, "The added vertex should be stored correctly in the graph"
        with pytest.raises(ValueError):
            graph.add_vertex(vertex_id=1, name="RRRR",
                             middle="", orientation=0, position=(0, 1))

    def test_add_meeple(self):
        graph = GraphData()
        graph.add_vertex(vertex_id=1, name="RRRR", middle="",
                         orientation=0, position=(0, 1))
        graph.add_meeple(Meeple(player_id=1, tile_id=1,
                         position=0, lands_components='R1'))
        assert len(graph.meeples) == 1, "One meeple should be added to the graph"
        assert graph.meeples.pop() == Meeple(player_id=1, tile_id=1, position=0,
                                             lands_components='R1'), "The added meeple should be stored correctly in the graph"
