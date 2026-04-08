"""Graph-backed game state for Carcassonne.

GraphData implements `IGraphData` and manages tile vertices, neighbors, and
related lookup helpers.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, List

from carcassonne.interfaces.i_graph_data import IGraphData
from carcassonne.datas.tiles_constants import EAST_DIR
from carcassonne.datas.tiles_constants import NORTH_DIR
from carcassonne.datas.tiles_constants import ORIENTATIONS
from carcassonne.datas.tiles_constants import SOUTH_DIR
from carcassonne.datas.tiles_constants import WEST_DIR
from carcassonne.datas.meeple_data import Meeple
from carcassonne.datas.tiles_info import TilesInfo
from carcassonne.datas.tiles_info import Tile

LAND_TYPES = ("C", "R", "F", "M", "S")

SIDE_DELTAS = {
    NORTH_DIR: (0, -1),
    EAST_DIR: (1, 0),
    SOUTH_DIR: (0, 1),
    WEST_DIR: (-1, 0),
}


@dataclass(init=False)
class Vertex:
    id: int
    name: str
    middle: str
    matrix: list[list]
    tile_dict: Dict[str, list]
    orientation: int = 0

    # Position of the vertex around the first vertex at (0, 0)
    position: tuple[int, int] = (0, 0)
    # Couples of (key = direction, value = neighbor vertex id)
    neighbors: Dict[int, int] = field(default_factory=dict)

    def __init__(
        self,
        id: int,
        name: str,
        middle: str,
        tile_dict: Dict[str, list],
        orientation: int = 0,
        position: tuple[int, int] = (0, 0),
    ) -> None:
        """Create one tile vertex and precompute its oriented matrix.

        Args:
            id: Unique tile identifier in the graph.
            name: Tile code (for example "CRFR" or "FSRS/m").
            middle: Middle feature marker used by scoring logic.
            tile_dict: Terrain groups for this tile definition.
            orientation: Rotation index in [0, 3].
            position: Board coordinates `(x, y)`.

        Returns:
            None.
        """
        self.id = id
        self.name = name
        self.middle = middle
        self.position = position
        self.orientation = orientation % ORIENTATIONS
        self.neighbors = {}
        self.tile_dict = tile_dict
        self.matrix = [["" for _ in range(3)] for _ in range(3)]
        self.build_matrix()

    def set_neighbor(self, orientation: int, neighbor_id: int) -> None:
        """Register one neighbor tile for a given side.

        Args:
            orientation: Side index in [0, 3].
            neighbor_id: Identifier of the adjacent tile.

        Returns:
            None.
        """
        if orientation not in range(ORIENTATIONS):
            raise ValueError(
                f"Orientation must be between 0 and {ORIENTATIONS - 1}"
            )
        self.neighbors[orientation] = neighbor_id

    def remove_neighbor(self, orientation: int) -> None:
        """Remove the neighbor mapping for one side if present.

        Args:
            orientation: Side index to clear.

        Returns:
            None.
        """
        if orientation in self.neighbors:
            del self.neighbors[orientation]

    def is_neighbor_free(self, position: int) -> bool:
        """Return whether a side currently has no neighbor.

        Args:
            position: Side index in [0, 3].

        Returns:
            True when the side has no mapped neighbor.
        """
        return position not in self.neighbors

    def rotate(self, k: int = 1) -> None:
        """Rotate the tile orientation clockwise.

        Args:
            k: Number of quarter-turns.

        Returns:
            None.
        """
        self.orientation = (self.orientation + k) % ORIENTATIONS

    def build_matrix(self) -> None:
        """Build the 3x3 terrain matrix for the current orientation.

        Returns:
            None. Mutates `self.matrix`.
        """
        dir_matrix = Tile.direction_matrix[self.orientation]
        for i in range(3):
            for j in range(3):
                dir = dir_matrix[i][j]
                for land in self.tile_dict.keys():
                    matched = False
                    for set in self.tile_dict[land]:
                        if dir in set:
                            self.matrix[i][j] = land
                            matched = True
                            break
                    if matched:
                        break

    def get_id(self) -> int:
        """Return this vertex identifier."""
        return self.id

    def get_name(self) -> str:
        """Return the tile code for this vertex."""
        return self.name

    def get_middle(self) -> str:
        """Return the middle feature marker for this tile."""
        return self.middle

    def get_orientation(self) -> int:
        """Return the current rotation index."""
        return self.orientation

    def get_position(self) -> tuple[int, int]:
        """Return board coordinates `(x, y)` for this tile."""
        return self.position

    def get_neighbors(self) -> Dict[int, int]:
        """Return a copy of neighbor mappings by side index."""
        return dict(self.neighbors)

    def get_matrix(self) -> list[list]:
        """Return the oriented 3x3 terrain matrix."""
        return self.matrix

    def get_tile_dict(self) -> Dict[str, list]:
        """Return terrain groups for this tile definition."""
        return self.tile_dict


class GraphData(IGraphData):
    def __init__(self) -> None:
        """Initialise graph storage, terrain components, and meeple list."""
        self.vertices: Dict[int, Vertex] = {}
        self.positions_to_vertex_id: Dict[tuple[int, int], int] = {}
        self.turn = 0
        # Lands components structure: {land_type: {set_name: [(tile_id,
        # [directions]), ...]}}
        self.lands_components: Dict[str, Dict[str, list]] = {}
        self.next_set_id: Dict[str, int] = {}  # Track next ID per land type
        self.meeples: List[Meeple] = []
        self.tiles_dict = TilesInfo().tiles
        self.initialize_land_components()

    def initialize_land_components(self) -> None:
        """Reset terrain-component containers and per-type set counters.

        Returns:
            None.
        """
        for land_type in LAND_TYPES:
            self.lands_components[land_type] = {}
            self.next_set_id[land_type] = 1

    def initialize_starting_tile(self, river: bool = False) -> None:
        """Initialize the first tile and its initial land components."""
        tile_name = "FFSF" if river else "CRFR"
        self.add_vertex(
            vertex_id=0,
            name=tile_name,
            middle="",
            orientation=0,
            position=(0, 0),
        )
        tile = self.tiles_dict[tile_name]
        for land in tile.tiles_lands.keys():
            for connected in tile.tiles_lands[land]:
                land_id = land + str(self.next_set_id[land])
                self.lands_components[land][land_id] = [(0, connected)]
                self.next_set_id[land] += 1

    def add_vertex(
        self,
        vertex_id: int,
        name: str,
        middle: str,
        orientation: int,
        position: tuple[int, int],
    ) -> None:
        """Create and insert one tile vertex, then connect its neighbors.

        Args:
            vertex_id: Unique tile identifier.
            name: Tile code.
            middle: Middle feature marker.
            orientation: Rotation index in [0, 3].
            position: Board coordinates `(x, y)`.

        Returns:
            None.
        """
        if vertex_id in self.vertices:
            raise ValueError(f"Vertex ID already exists : {vertex_id}")

        if position is None:
            raise ValueError("Error in getting position")

        vertex = Vertex(
            id=vertex_id,
            name=name,
            middle=middle,
            tile_dict=self.tiles_dict[name].tiles_lands,
            orientation=orientation % ORIENTATIONS,
            position=position,
        )
        self.vertices[vertex_id] = vertex
        self.positions_to_vertex_id[position] = vertex_id

        self.turn += 1

        self.compute_neighbors(vertex_id)

    def add_meeple(self, meeple: Meeple) -> None:
        """Append one placed meeple to the board list.

        Args:
            meeple: Meeple placement data.

        Returns:
            None.
        """
        self.meeples.append(meeple)

    def compute_neighbors(self, vertex_id: int) -> None:
        """Compute and register adjacent tiles for one vertex.

        Args:
            vertex_id: Identifier of the vertex to link.

        Returns:
            None.
        """
        vertex = self.get_vertex(vertex_id)
        if vertex is None:
            raise ValueError(f"Vertex ID not found : {vertex_id}")

        for side in range(ORIENTATIONS):
            potential_neighbor_pos = self.get_adjacent_position(
                vertex_id, side
            )
            if potential_neighbor_pos is None:
                continue
            neighbor_id = self.positions_to_vertex_id.get(
                potential_neighbor_pos
            )
            if neighbor_id is not None:
                self.set_neighbor(vertex_id, side, neighbor_id)

    def set_neighbor(
        self,
        vertex_id: int,
        orientation: int,
        neighbor_id: int,
        bidirectional: bool = True,
    ) -> None:
        """Link two vertices as neighbors on a given side.

        Args:
            vertex_id: Source vertex identifier.
            orientation: Side index on source vertex.
            neighbor_id: Target vertex identifier.
            bidirectional: Also set the opposite side on target when True.

        Returns:
            None.
        """
        if vertex_id not in self.vertices or neighbor_id not in self.vertices:
            raise ValueError("Vertex ID or neighbor ID not found")
        self.vertices[vertex_id].set_neighbor(orientation, neighbor_id)
        if bidirectional:
            opposite_ori = (orientation + (ORIENTATIONS // 2)) % ORIENTATIONS
            self.vertices[neighbor_id].set_neighbor(opposite_ori, vertex_id)

    def remove_vertex(self, vertex_id: int) -> None:
        """Remove one vertex and clean all dependent graph references.

        Args:
            vertex_id: Identifier of the tile to remove.

        Returns:
            None.
        """
        if vertex_id not in self.vertices:
            raise ValueError(f"Vertex ID not found : {vertex_id}")
        removed_position = self.vertices[vertex_id].get_position()
        for vertex in self.vertices.values():
            for ori, id in list(vertex.neighbors.items()):
                if id == vertex_id:
                    vertex.remove_neighbor(ori)
                    self.turn -= 1
        del self.vertices[vertex_id]
        self.positions_to_vertex_id.pop(removed_position, None)
        # Remove all lands_components entries referencing this tile so that
        # the same tile ID can be reused on the next placement without causing
        # duplicate component entries and inflated scores.
        for land_type in list(self.lands_components.keys()):
            for comp_name in list(self.lands_components[land_type].keys()):
                self.lands_components[land_type][comp_name] = [
                    (tid, drg)
                    for tid, drg in self.lands_components[land_type][comp_name]
                    if tid != vertex_id
                ]
                if not self.lands_components[land_type][comp_name]:
                    del self.lands_components[land_type][comp_name]

    def remove_meeple(self, tile_id: int, players: dict[int, Any]) -> None:
        """Remove the meeple placed on a tile and refund it to its owner.

        Args:
            tile_id: Tile identifier where the meeple was placed.
            players: Players indexed by identifier.

        Returns:
            None.
        """
        for meeple in self.meeples:
            if meeple.tile_id == tile_id:
                self.meeples.remove(meeple)
                meeple_owner = players.get(meeple.player_id)
                if meeple_owner is not None:
                    meeple_owner.add_meeple()  # Return the meeple to owner
                break

    def get_vertex(self, vertex_id: int) -> Optional[Vertex]:
        """Return one vertex by id, or None when absent."""
        return self.vertices.get(vertex_id)

    def get_vertices(self) -> Dict[int, Vertex]:
        """Return a shallow copy of all graph vertices."""
        return dict(self.vertices)

    def get_vertices_data(self) -> dict[int, dict]:
        """Return all vertex payloads required by the GUI.

        Returns:
            Mapping `{vertex_id: serialized_vertex_data}`.
        """
        return {
            vertex_id: self._vertex_to_gui_data(vertex)
            for vertex_id, vertex in self.vertices.items()
        }

    def get_vertex_data(self, vertex: Vertex) -> dict[int, dict]:
        """Return one vertex payload in the same shape as GUI bulk data.

        Args:
            vertex: Vertex object to serialize.

        Returns:
            Mapping `{vertex_id: serialized_vertex_data}`.
        """
        return {
            vertex.get_id(): {
                **self._vertex_to_gui_data(vertex),
            }
        }

    @staticmethod
    def _vertex_to_gui_data(vertex: Vertex) -> dict:
        """Serialize one vertex to the GUI-friendly payload format.

        Args:
            vertex: Vertex object to serialize.

        Returns:
            Dictionary containing id, coordinates, tile name, middle, and
            orientation.
        """
        x, y = vertex.get_position()
        return {
            "id": vertex.get_id(),
            "x": x,
            "y": y,
            "name": vertex.get_name(),
            "middle": vertex.get_middle(),
            "orientation": vertex.get_orientation(),
        }

    def get_adjacent_position(
        self, vertex_id: int, side: int
    ) -> Optional[tuple[int, int]]:
        """Return adjacent coordinates from a vertex id and side.

        Args:
            vertex_id: Identifier of the origin vertex.
            side: Side index in [0, 3].

        Returns:
            Adjacent coordinates, or None if the vertex does not exist.
        """
        vertex = self.get_vertex(vertex_id)
        if vertex is None:
            return None
        return GraphData.get_adjacent_position_from(
            vertex.get_position(), side
        )

    @staticmethod
    def get_adjacent_position_from(
        position: tuple[int, int], side: int
    ) -> Optional[tuple[int, int]]:
        """Return adjacent coordinates from a raw board position.

        Args:
            position: Origin coordinates `(x, y)`.
            side: Side index in [0, 3].

        Returns:
            Adjacent coordinates.

        Raises:
            ValueError: When `side` is not in [0, 3].
        """
        if side not in SIDE_DELTAS:
            raise ValueError(f"Invalid side: {side}")
        dx, dy = SIDE_DELTAS[side]
        x, y = position
        return (x + dx, y + dy)

    def get_neighbors(self, vertex_id: int) -> Dict[int, int]:
        """Return neighbor mappings for a vertex.

        Args:
            vertex_id: Vertex identifier.

        Returns:
            Mapping `{side_index: neighbor_vertex_id}`.
        """
        if vertex_id not in self.vertices:
            return {}
        return self.vertices[vertex_id].get_neighbors()

    def get_turn_number(self) -> int:
        """Return the internal turn counter."""
        return self.turn

    def get_meeples(self) -> List[Meeple]:
        """Return the list of currently placed meeples."""
        return self.meeples

    def set_meeples(self, meeples_list: List[Meeple]) -> None:
        """Replace all placed meeples with the provided list.

        Args:
            meeples_list: Meeple placements to set as current state.

        Returns:
            None.
        """
        self.meeples.clear()
        self.meeples.extend(meeples_list)

    def reset_graph(self):
        """Reset the whole graph state to an empty board baseline.

        Returns:
            None.
        """
        self.vertices.clear()
        self.positions_to_vertex_id.clear()
        self.lands_components.clear()
        self.next_set_id.clear()
        self.meeples.clear()
        self.turn = 0
        # Resetting the graph with the starting tile (CRFR) as a vertex in the
        # graph
        self.initialize_land_components()

    def get_vertex_orientation(self, vertex_id: int) -> int:
        """Return orientation of a vertex by id.

        Args:
            vertex_id: Vertex identifier.

        Returns:
            Orientation index in [0, 3].
        """
        vertex = self.get_vertex(vertex_id)
        if vertex is None:
            raise ValueError(f"Vertex ID not found : {vertex_id}")
        return vertex.get_orientation()

    def find_neighbor_at(
        self, x: int, y: int
    ) -> tuple[Optional[int], Optional[int]]:
        """Find one neighboring tile around a target board position.

        Args:
            x: X coordinate of the target position.
            y: Y coordinate of the target position.

        Returns:
            Tuple `(vertex_id, side_relative_to_new_tile)` where `side`
            identifies the side of the new tile touching that neighbor.
            Returns `(None, None)` when no neighbor is found.
        """
        for side, (dx, dy) in SIDE_DELTAS.items():
            neighbor_position = (x + dx, y + dy)
            vertex_id = self.positions_to_vertex_id.get(neighbor_position)
            if vertex_id is not None:
                # side is the direction from the new tile to this neighbor;
                # opposite_side is the side of the neighbor that faces back
                opposite_side = (side + 2) % 4
                return vertex_id, opposite_side

        return None, None
