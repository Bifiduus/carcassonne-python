from types import SimpleNamespace

import pytest

from carcassonne.business_logic.rules_manager import RulesManager
from carcassonne.datas.graph_data import GraphData
from carcassonne.datas.starting_tile import initialize_starting_tile
from carcassonne.datas.tiles_info import TilesInfo


class DummyRiverManager:
    def __init__(self, active: bool = False, river_over: bool = True, turn_ok: bool = True) -> None:
        self.active = active
        self.turn_ok = turn_ok
        self.game_data = SimpleNamespace(is_river_over=lambda: river_over)

    def is_river_active(self) -> bool:
        return self.active

    def check_river_turn(self, move_parts) -> bool:
        return self.turn_ok


class DummyNeighborVertex:
    def __init__(self, position, matrix) -> None:
        self.position = position
        self.matrix = matrix

    def get_position(self):
        return self.position

    def get_matrix(self):
        return self.matrix


class DummyGraphForSides:
    def __init__(self, vertices) -> None:
        self.vertices = vertices

    def get_adjacent_position_from(self, position, side):
        x, y = position
        offsets = {
            0: (0, -1),
            1: (1, 0),
            2: (0, 1),
            3: (-1, 0),
        }
        dx, dy = offsets[side]
        return (x + dx, y + dy)

    def get_vertices(self):
        return self.vertices


class DummyMeeple:
    def __init__(
        self,
        lands_components: str,
        player_id: int,
        tile_id: int = 1,
        position_label: str = "N",
    ) -> None:
        self.lands_components = lands_components
        self.player_id = player_id
        self.tile_id = tile_id
        self._position_label = position_label

    def get_position_label(self) -> str:
        return self._position_label


class DummyVertexForMeeple:
    def __init__(self, land_type: str, name: str = "CFFF") -> None:
        self.land_type = land_type
        self.name = name

    def get_matrix(self):
        matrix = [["" for _ in range(3)] for _ in range(3)]
        matrix[0][1] = self.land_type
        return matrix

    def get_name(self):
        return self.name


class DummyGraphForMeeple:
    def __init__(
        self,
        tile_pos=(0, -1),
        land_type="C",
        component_name="C1",
        meeples=None,
    ) -> None:
        self.tile_pos = tile_pos
        self.land_type = land_type
        self.vertices = {0: object()}
        self.meeples = list(meeples or [])
        self.removed_vertices = []
        if component_name is None:
            self.lands_components = {land_type: {}}
        else:
            self.lands_components = {
                land_type: {component_name: [(1, ["N"])]}
            }

    def get_adjacent_position(self, vertex_id, side):
        return self.tile_pos

    def get_vertices(self):
        return dict(self.vertices)

    def add_vertex(self, vertex_id, name, middle, orientation, position) -> None:
        self.vertices[vertex_id] = DummyVertexForMeeple(self.land_type)

    def get_vertex(self, vertex_id):
        return self.vertices[vertex_id]

    def get_meeples(self):
        return list(self.meeples)

    def remove_vertex(self, vertex_id) -> None:
        self.removed_vertices.append(vertex_id)
        self.vertices.pop(vertex_id, None)


class DummyGraphLogic:
    def add_lands_components(self, tile_id, graph, tiles_info) -> None:
        return None


class DummyVertexForLegal:
    def __init__(self, free: bool = True) -> None:
        self.free = free

    def is_neighbor_free(self, side: int) -> bool:
        return self.free


class DummyGraphForLegal:
    def __init__(self, free: bool = True) -> None:
        self.vertices = {0: DummyVertexForLegal(free)}

    def get_vertices(self):
        return self.vertices

    def get_adjacent_position(self, vertex_id, side):
        return (0, -1)


def test_rules_manager_helper_methods() -> None:
    manager = RulesManager(TilesInfo())

    numbers, target_side = manager._extract_placement_data("12N3")
    assert numbers == [12, 3]
    assert target_side == "N"

    graph = SimpleNamespace(
        lands_components={"C": {"C1": [(4, ["N", "E"])]}}
    )
    assert manager._find_component_set_name(graph, "C", 4, "E") == "C1"
    assert manager._find_component_set_name(graph, "C", 4, "W") is None

    assert manager._get_graph_logic() is manager._get_graph_logic()


@pytest.mark.parametrize(
    ("move", "expected"),
    [
        ("CFFF/0N0", True),
        ("FFFF/m/0N0", True),
        ("CFFF/0N0/N", True),
        (None, False),
        ("CFFF", False),
        ("XXXX/0N0", False),
        ("FFFF/x/0N0", False),
        ("CFFF/2N0", False),
        ("CFFF/0NE0", False),
        ("CFFF/0X0", False),
        ("CFFF/0N4", False),
        ("CFFF/0N0/INVALID", False),
    ],
)
def test_is_correctly_formed_move_covers_valid_and_invalid_formats(move, expected) -> None:
    manager = RulesManager(TilesInfo())
    graph = GraphData()
    initialize_starting_tile(graph)

    assert manager.is_correctly_formed_move(move, graph) is expected


def test_are_equal_sides_rejects_mismatch_and_missing_river_connection() -> None:
    manager = RulesManager(TilesInfo())
    mismatch_matrix = [["" for _ in range(3)] for _ in range(3)]
    mismatch_matrix[1][0] = "R"
    graph = DummyGraphForSides(
        {1: DummyNeighborVertex((1, 0), mismatch_matrix)}
    )

    assert (
        manager.are_equal_sides(
            "CFFF",
            (0, 0),
            0,
            graph,
            DummyRiverManager(active=False),
        )
        is False
    )

    empty_graph = DummyGraphForSides({})
    assert (
        manager.are_equal_sides(
            "CFFF",
            (0, 0),
            0,
            empty_graph,
            DummyRiverManager(active=True, river_over=False),
        )
        is False
    )


def test_are_equal_sides_accepts_matching_river_extension() -> None:
    manager = RulesManager(TilesInfo())
    neighbor_matrix = [["" for _ in range(3)] for _ in range(3)]
    neighbor_matrix[1][0] = "S"
    graph = DummyGraphForSides(
        {1: DummyNeighborVertex((1, 0), neighbor_matrix)}
    )

    assert (
        manager.are_equal_sides(
            "FSFF",
            (0, 0),
            0,
            graph,
            DummyRiverManager(active=True, river_over=False),
        )
        is True
    )


def test_can_place_meeple_on_tile_side_covers_success_and_rejections(monkeypatch) -> None:
    manager = RulesManager(TilesInfo())
    monkeypatch.setattr(manager, "_get_graph_logic", lambda: DummyGraphLogic())

    assert (
        manager.can_place_meeple_on_tile_side(
            ["CFFF", "0N0", "N"],
            2,
            DummyGraphForMeeple(tile_pos=None),
        )
        is False
    )

    assert (
        manager.can_place_meeple_on_tile_side(
            ["FSFS", "0N0", "N"],
            2,
            DummyGraphForMeeple(land_type="S", component_name="S1"),
        )
        is False
    )

    assert (
        manager.can_place_meeple_on_tile_side(
            ["CFFF", "0N0", "N"],
            2,
            DummyGraphForMeeple(component_name=None),
        )
        is False
    )

    conflict_graph = DummyGraphForMeeple(
        meeples=[DummyMeeple("C1", 7)],
    )
    assert (
        manager.can_place_meeple_on_tile_side(
            ["CFFF", "0N0", "N"],
            2,
            conflict_graph,
        )
        is False
    )

    same_player_graph = DummyGraphForMeeple(
        meeples=[DummyMeeple("C1", 3)],
    )
    assert (
        manager.can_place_meeple_on_tile_side(
            ["CFFF", "0N0", "N"],
            2,
            same_player_graph,
            current_player_id=3,
        )
        is True
    )


def test_can_place_meeple_uses_resolved_component_not_stale_label(
    monkeypatch,
) -> None:
    manager = RulesManager(TilesInfo())
    monkeypatch.setattr(manager, "_get_graph_logic", lambda: DummyGraphLogic())

    # Existing meeple stores stale component label C1 but is actually on C2.
    # New simulated tile would also resolve to C1, so placement should stay
    # valid when we resolve component from tile+position.
    graph = DummyGraphForMeeple(
        component_name="C1",
        meeples=[DummyMeeple("C1", 7, tile_id=0, position_label="N")],
    )
    graph.vertices[0] = DummyVertexForMeeple("C", name="CFFF")
    graph.lands_components = {
        "C": {
            "C1": [(1, ["N"])],
            "C2": [(0, ["N"])],
        }
    }

    assert (
        manager.can_place_meeple_on_tile_side(
            ["CFFF", "0N0", "N"],
            2,
            graph,
        )
        is True
    )


def test_is_legal_move_covers_major_branch_failures_and_success(monkeypatch) -> None:
    manager = RulesManager(TilesInfo())
    river_manager = DummyRiverManager()

    monkeypatch.setattr(manager.tiles_info, "is_tile_left", lambda tile_code: False)
    assert manager.is_legal_move(["CFFF", "0N0"], DummyGraphForLegal(), river_manager) is False

    monkeypatch.setattr(
        manager.tiles_info,
        "is_tile_left",
        lambda tile_code: tile_code == "FFFF/m",
    )
    monkeypatch.setattr(manager, "are_equal_sides", lambda *args, **kwargs: True)
    assert manager.is_legal_move(["FFFF", "m", "0N0"], DummyGraphForLegal(), river_manager) is True

    monkeypatch.setattr(manager.tiles_info, "is_tile_left", lambda tile_code: True)
    assert manager.is_legal_move(["CFFF", "0N0"], DummyGraphForLegal(free=False), river_manager) is False

    monkeypatch.setattr(manager, "are_equal_sides", lambda *args, **kwargs: False)
    assert manager.is_legal_move(["CFFF", "0N0"], DummyGraphForLegal(), river_manager) is False

    monkeypatch.setattr(manager, "are_equal_sides", lambda *args, **kwargs: True)
    river_manager.turn_ok = False
    assert manager.is_legal_move(["CFFF", "0N0"], DummyGraphForLegal(), river_manager) is False

    river_manager.turn_ok = True
    monkeypatch.setattr(
        manager,
        "can_place_meeple_on_tile_side",
        lambda *args, **kwargs: False,
    )
    assert manager.is_legal_move(["CFFF", "0N0", "N"], DummyGraphForLegal(), river_manager) is False

    monkeypatch.setattr(
        manager,
        "can_place_meeple_on_tile_side",
        lambda *args, **kwargs: True,
    )
    assert manager.is_legal_move(["CFFF", "0N0", "N"], DummyGraphForLegal(), river_manager) is True


def test_check_move_short_circuits_and_delegates(monkeypatch) -> None:
    manager = RulesManager(TilesInfo())
    graph = DummyGraphForLegal()
    river_manager = DummyRiverManager()

    monkeypatch.setattr(manager, "is_correctly_formed_move", lambda move, graph: False)
    assert manager.check_move("CFFF/0N0", graph, river_manager) is False

    monkeypatch.setattr(manager, "is_correctly_formed_move", lambda move, graph: True)
    monkeypatch.setattr(
        manager,
        "is_legal_move",
        lambda move_parts, graph, river_manager, current_player_id=None: True,
    )
    assert manager.check_move("CFFF/0N0", graph, river_manager, current_player_id=1) is True


@pytest.mark.parametrize(
    ("move", "expected_reason"),
    [
        (None, "move must be a string"),
        ("CFFF", "move format is invalid"),
        ("XXXX/0N0", "tile code is invalid"),
        ("FFFF/x/0N0", "tile center variant is invalid"),
        ("CFFF/00", "placement format is invalid"),
        ("CFFF/0X0", "target side is invalid"),
        ("CFFF/0N4", "tile rotation is invalid"),
        ("CFFF/0N0/INVALID", "meeple position is invalid"),
    ],
)
def test_explain_invalid_move_reports_format_and_syntax_issues(
    move,
    expected_reason,
) -> None:
    manager = RulesManager(TilesInfo())
    graph = GraphData()
    initialize_starting_tile(graph)

    assert manager.explain_invalid_move(
        move,
        graph,
        DummyRiverManager(),
    ) == expected_reason


def test_explain_invalid_move_reports_unavailable_tile(monkeypatch) -> None:
    manager = RulesManager(TilesInfo())
    graph = GraphData()
    initialize_starting_tile(graph)
    monkeypatch.setattr(manager.tiles_info, "is_tile_left", lambda _: False)

    assert (
        manager.explain_invalid_move("CFFF/0N0", graph, DummyRiverManager())
        == "tile CFFF is not available"
    )


def test_explain_invalid_move_reports_occupied_side(monkeypatch) -> None:
    manager = RulesManager(TilesInfo())
    graph = DummyGraphForLegal(free=False)
    monkeypatch.setattr(manager.tiles_info, "is_tile_left", lambda _: True)

    assert (
        manager.explain_invalid_move("CFFF/0N0", graph, DummyRiverManager())
        == "target side is already occupied"
    )


def test_explain_invalid_move_reports_neighbor_side_mismatch(monkeypatch) -> None:
    manager = RulesManager(TilesInfo())
    graph = DummyGraphForLegal()
    monkeypatch.setattr(manager.tiles_info, "is_tile_left", lambda _: True)
    monkeypatch.setattr(manager, "are_equal_sides", lambda *args, **kwargs: False)

    assert (
        manager.explain_invalid_move("CFFF/0N0", graph, DummyRiverManager())
        == "tile sides do not match neighboring tiles"
    )


def test_explain_invalid_move_reports_river_rule_violation(monkeypatch) -> None:
    manager = RulesManager(TilesInfo())
    graph = DummyGraphForLegal()
    monkeypatch.setattr(manager.tiles_info, "is_tile_left", lambda _: True)
    monkeypatch.setattr(manager, "are_equal_sides", lambda *args, **kwargs: True)

    assert (
        manager.explain_invalid_move(
            "CFFF/0N0",
            graph,
            DummyRiverManager(turn_ok=False),
        )
        == "river placement rules are violated"
    )


def test_explain_invalid_move_delegates_to_meeple_failure_explanation(
    monkeypatch,
) -> None:
    manager = RulesManager(TilesInfo())
    graph = DummyGraphForLegal()
    monkeypatch.setattr(manager.tiles_info, "is_tile_left", lambda _: True)
    monkeypatch.setattr(manager, "are_equal_sides", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        manager,
        "can_place_meeple_on_tile_side",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(
        manager,
        "explain_meeple_placement_failure",
        lambda *args, **kwargs: "component C1 already contains a meeple",
    )

    assert (
        manager.explain_invalid_move(
            "CFFF/0N0/N",
            graph,
            DummyRiverManager(),
        )
        == "component C1 already contains a meeple"
    )


def test_explain_meeple_placement_failure_covers_all_specific_reasons(
    monkeypatch,
) -> None:
    manager = RulesManager(TilesInfo())
    monkeypatch.setattr(manager, "_get_graph_logic", lambda: DummyGraphLogic())

    assert manager.explain_meeple_placement_failure(
        ["CFFF", "0N0", "N"],
        2,
        DummyGraphForMeeple(tile_pos=None),
    ) == "target tile position is invalid"

    assert manager.explain_meeple_placement_failure(
        ["FSFS", "0N0", "N"],
        2,
        DummyGraphForMeeple(land_type="S", component_name="S1"),
    ) == "meeples cannot be placed on river segments"

    assert manager.explain_meeple_placement_failure(
        ["CFFF", "0N0", "N"],
        2,
        DummyGraphForMeeple(component_name=None),
    ) == "selected meeple position does not map to a component"

    assert (
        manager.explain_meeple_placement_failure(
            ["CFFF", "0N0", "N"],
            2,
            DummyGraphForMeeple(meeples=[DummyMeeple("C1", 7)]),
        )
        == "component C1 already contains a meeple"
    )

    assert manager.explain_meeple_placement_failure(
        ["CFFF", "0N0", "N"],
        2,
        DummyGraphForMeeple(meeples=[DummyMeeple("C1", 3)]),
        current_player_id=3,
    ) == "meeple placement is invalid"


def test_explain_meeple_failure_ignores_stale_component_labels(monkeypatch) -> None:
    manager = RulesManager(TilesInfo())
    monkeypatch.setattr(manager, "_get_graph_logic", lambda: DummyGraphLogic())

    graph = DummyGraphForMeeple(
        component_name="C1",
        meeples=[DummyMeeple("C1", 7, tile_id=0, position_label="N")],
    )
    graph.vertices[0] = DummyVertexForMeeple("C", name="CFFF")
    graph.lands_components = {
        "C": {
            "C1": [(1, ["N"])],
            "C2": [(0, ["N"])],
        }
    }

    assert (
        manager.explain_meeple_placement_failure(
            ["CFFF", "0N0", "N"],
            2,
            graph,
        )
        == "meeple placement is invalid"
    )
