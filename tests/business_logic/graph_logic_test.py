from types import SimpleNamespace

from carcassonne.business_logic.graph_logic import GraphLogic
from carcassonne.datas.meeple_data import Meeple
from carcassonne.datas.tiles_info import Tile


class DummyTilesInfo:
    """Mock TilesInfo for testing."""

    def __init__(self, tiles_dict=None):
        self.tiles = tiles_dict or {}

    def get_tile_definition(self, tile_code: str):
        return self.tiles.get(tile_code)


class DummyVertex:
    def __init__(
        self, name: str, orientation: int = 0, neighbors=None
    ) -> None:
        self.name = name
        self.orientation = orientation
        self.neighbors = dict(neighbors or {})

    def get_neighbors(self):
        return dict(self.neighbors)

    def get_orientation(self):
        return self.orientation


class DummyGraph:
    def __init__(
        self,
        lands_components=None,
        vertices=None,
        next_set_id=None,
        meeples=None,
    ) -> None:
        self.lands_components = lands_components or {
            "C": {},
            "R": {},
            "F": {},
            "M": {},
            "S": {},
        }
        self.vertices = vertices or {}
        self.meeples = list(meeples or [])
        self.next_set_id = next_set_id or {
            "C": 1,
            "R": 1,
            "F": 1,
            "M": 1,
            "S": 1,
        }

    def get_vertex(self, vertex_id: int):
        return self.vertices.get(vertex_id)


def test_graph_logic_index_and_group_helpers_cover_lookup_creation_and_replacement(
):
    logic = GraphLogic()
    tile_def = Tile("CUR", {"C": [["N"]], "F": [["NW", "NE"]]})
    graph = DummyGraph(
        lands_components={
            "C": {"C1": [(1, ["N"])]},
            "R": {"R1": [(2, ["E"])]},
            "F": {},
            "M": {},
            "S": {},
        },
        next_set_id={"C": 2, "R": 2, "F": 1, "M": 1, "S": 1},
    )

    linked, connection_count, land_type = logic._initialize_group_tracking(
        tile_def
    )
    lands_index = GraphLogic._build_lands_set_index(graph)
    original_city_set = graph.lands_components["C"]["C1"]

    assert linked == {("N",): False, ("NW", "NE"): False}
    assert connection_count == {("N",): 0, ("NW", "NE"): 0}
    assert land_type == {("N",): "C", ("NW", "NE"): "F"}
    assert (
        GraphLogic._find_component_set("C", 1, ["N"], graph, lands_index)
        is original_city_set
    )
    assert GraphLogic._find_component_set("R", 2, ["E"], graph) == [(2, ["E"])]
    assert GraphLogic._find_component_set("C", 9, ["N"], graph) is None

    GraphLogic._index_set_entry(lands_index, "C", 1, ["N"], original_city_set)
    assert lands_index[("C", 1, ("N",))] == [original_city_set]

    replacement_set = [(1, ["N"]), (3, ["S"])]
    GraphLogic._replace_index_set_reference(
        lands_index,
        "C",
        1,
        ["N"],
        original_city_set,
        replacement_set,
    )
    assert lands_index[("C", 1, ("N",))] == [replacement_set]
    assert GraphLogic._get_next_set_name("F", graph) == "F1"
    assert graph.next_set_id["F"] == 2
    assert GraphLogic._find_land_and_group_for_side(tile_def, "NE") == (
        "F",
        ["NW", "NE"],
    )
    assert GraphLogic._find_land_and_group_for_side(tile_def, "S") == (
        None,
        None,
    )
    assert (
        GraphLogic._find_neighbor_group(Tile("N", {"C": [["S"]]}), "C", "S")
        == ["S"]
    )
    assert (
        GraphLogic._find_neighbor_group(Tile("N", {"C": [["S"]]}), "F", "S")
        is None
    )


def test_collect_and_merge_set_names_updates_components_and_index() -> None:
    logic = GraphLogic()
    graph = DummyGraph(
        lands_components={
            "C": {
                "C1": [(1, ["N"])],
                "C2": [(2, ["E"])],
            },
            "R": {},
            "F": {},
            "M": {},
            "S": {},
        },
        meeples=[
            Meeple(
                player_id=0, tile_id=1, position=0, lands_components="C1"
            ),
            Meeple(
                player_id=1, tile_id=2, position=1, lands_components="C2"
            ),
        ],
    )
    lands_index = GraphLogic._build_lands_set_index(graph)
    lands_index[("C", 1, ("N",))] = [
        graph.lands_components["C"]["C1"],
        graph.lands_components["C"]["C2"],
    ]

    assert logic._collect_sets_to_merge(
        "C", 1, ("N",), graph, lands_index
    ) == ["C1", "C2"]

    logic._merge_set_names("C", ["C1", "C2"], graph, lands_index)

    assert "C2" not in graph.lands_components["C"]
    assert graph.lands_components["C"]["C1"] == [(1, ["N"]), (2, ["E"])]
    assert lands_index[("C", 2, ("E",))] == [graph.lands_components["C"]["C1"]]
    assert [meeple.lands_components for meeple in graph.meeples] == [
        "C1",
        "C1",
    ]


def test_handle_cardinal_corner_and_special_corner_connections_link_existing_sets(
):
    logic = GraphLogic()

    cardinal_graph = DummyGraph(
        lands_components={
            "C": {"C1": [(2, ["S"])]},
            "R": {},
            "F": {},
            "M": {},
            "S": {},
        },
        vertices={2: DummyVertex("NEI")},
    )
    cardinal_tile = Tile("CUR", {"C": [["N"]]})
    cardinal_info = DummyTilesInfo(
        {"NEI": Tile("NEI", {"C": [["S"]]})}
    )
    linked, counts, _ = logic._initialize_group_tracking(cardinal_tile)
    lands_index = GraphLogic._build_lands_set_index(cardinal_graph)

    logic.handle_cardinal_connection(
        1,
        2,
        "N",
        "N",
        cardinal_graph,
        cardinal_tile,
        cardinal_info,
        linked,
        counts,
        lands_index,
    )

    assert cardinal_graph.lands_components["C"]["C1"][-1] == (1, ["N"])
    assert linked[("N",)] is True
    assert counts[("N",)] == 1

    corner_graph = DummyGraph(
        lands_components={
            "C": {},
            "R": {},
            "F": {"F1": [(2, ["SW"])]},
            "M": {},
            "S": {},
        },
        vertices={2: DummyVertex("NEI")},
    )
    corner_tile = Tile("CUR", {"F": [["NW"]]})
    corner_info = DummyTilesInfo(
        {"NEI": Tile("NEI", {"F": [["SW"]]})}
    )
    linked, counts, _ = logic._initialize_group_tracking(corner_tile)
    lands_index = GraphLogic._build_lands_set_index(corner_graph)

    logic.handle_corner_connection(
        1,
        2,
        "NW",
        "NW",
        corner_graph,
        corner_tile,
        corner_info,
        0,
        linked,
        counts,
        lands_index,
    )

    assert corner_graph.lands_components["F"]["F1"][-1] == (1, ["NW"])
    assert linked[("NW",)] is True
    assert counts[("NW",)] == 1

    special_graph = DummyGraph(
        lands_components={
            "C": {"C1": [(2, ["SW"])]},
            "R": {},
            "F": {},
            "M": {},
            "S": {},
        },
        vertices={2: DummyVertex("NEI")},
    )
    special_tile = Tile("CUR", {"C": [["NW"]]}, {"NW": ["C", "F"]})
    special_info = DummyTilesInfo(
        {"NEI": Tile("NEI", {"C": [["SW"]]})}
    )
    linked, counts, _ = logic._initialize_group_tracking(special_tile)
    lands_index = GraphLogic._build_lands_set_index(special_graph)

    logic.handle_special_corner_connection(
        1,
        0,
        2,
        "NW",
        "NW",
        special_graph,
        special_tile,
        special_info,
        ["C", "F"],
        0,
        linked,
        counts,
        lands_index,
    )

    assert special_graph.lands_components["C"]["C1"][-1] == (1, ["NW"])
    assert linked[("NW",)] is True
    assert counts[("NW",)] == 1


def test_add_lands_components_creates_unlinked_groups_and_handles_missing_data(
) -> None:
    logic = GraphLogic()
    graph = DummyGraph()
    tiles_info = DummyTilesInfo(
        {
            "CUR": Tile(
                "CUR",
                {
                    "C": [["N"]],
                    "F": [["S", "SE", "SW"]],
                },
            )
        }
    )

    logic.add_lands_components(99, graph, tiles_info)

    graph.vertices[1] = DummyVertex("UNKNOWN")
    logic.add_lands_components(1, graph, tiles_info)
    assert graph.lands_components == {
        "C": {},
        "R": {},
        "F": {},
        "M": {},
        "S": {},
    }

    graph.vertices[1] = DummyVertex("CUR")
    logic.add_lands_components(1, graph, tiles_info)

    assert graph.lands_components["C"]["C1"] == [(1, ["N"])]
    assert graph.lands_components["F"]["F1"] == [(1, ["S", "SE", "SW"])]
