"""Graph-backed game state for Carcassonne.

GraphData implements `IGraphData` and manages tile vertices, neighbors, and
related lookup helpers.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List

from carcassonne.business_logic.interfaces.i_graph_data import IGraphData
from carcassonne.business_logic.player import Player
from carcassonne.datas.meeple_data import Meeple
from carcassonne.datas.tiles_info import TilesInfo
from carcassonne.datas.tiles_info import Tile

NORTH_DIR = 0
EAST_DIR = 1
SOUTH_DIR = 2
WEST_DIR = 3

ORIENTATIONS = 4

OPPOSITE = {"N": "S", "S": "N", "E": "W", "W": "E"}
NORTHWEST_MATRIX = (0, 0)
NORTH_MATRIX = (0, 1)
NORTHEAST_MATRIX = (0, 2)
WEST_MATRIX = (1, 0)
CENTER_MATRIX = (1, 1)
EAST_MATRIX = (1, 2)
SOUTHWEST_MATRIX = (2, 0)
SOUTH_MATRIX = (2, 1)
SOUTHEAST_MATRIX = (2, 2)


@dataclass
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
        self.id = id
        self.name = name
        self.middle = middle
        self.position = position
        self.orientation = orientation % ORIENTATIONS
        self.neighbors = {}
        self.tile_dict = tile_dict
        # Initialize a 4x4 matrix for the vertex before building it
        self.matrix = [["" for _ in range(3)] for _ in range(3)]
        self.build_matrix()

    def set_neighbor(self, orientation: int, neighbor_id: int) -> None:
        if orientation not in range(ORIENTATIONS):
            raise ValueError(
                f"Orientation must be between 0 and {ORIENTATIONS - 1}"
            )
        self.neighbors[orientation] = neighbor_id

    def remove_neighbor(self, orientation: int) -> None:
        if orientation in self.neighbors:
            del self.neighbors[orientation]

    def is_neighbor_free(self, position: int) -> bool:
        return position not in self.neighbors

    def rotate(self, k: int = 1) -> None:
        self.orientation = (self.orientation + k) % ORIENTATIONS

    def build_matrix(self) -> None:
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
        return self.id

    def get_name(self) -> str:
        return self.name

    def get_middle(self) -> str:
        return self.middle

    def get_orientation(self) -> int:
        return self.orientation

    def get_position(self) -> tuple[int, int]:
        return self.position

    def get_neighbors(self) -> Dict[int, int]:
        return dict(self.neighbors)

    def get_matrix(self) -> list[list]:
        return self.matrix

    def get_tile_dict(self) -> Dict[str, list]:
        return self.tile_dict


class GraphData(IGraphData):
    def __init__(self) -> None:
        self.vertices: Dict[int, Vertex] = {}
        self.turn = 0
        # Lands components structure: {land_type: {set_name: [(tile_id,
        # [directions]), ...]}}
        self.lands_components: Dict[str, Dict[str, list]] = {}
        self.next_set_id: Dict[str, int] = {}  # Track next ID per land type
        # List of meeples placed on the board
        self.meeples: List[Meeple] = []
        self.tiles_dict = TilesInfo().tiles
        # Adding the starting tile (CRFR) as a vertex in the graph
        self.initialize_land_components()
        self.initialize_starting_tile()

    def initialize_land_components(self) -> None:
        # Initialize land components for the starting tile (CRFR)
        self.lands_components["C"] = {}
        self.lands_components["R"] = {}
        self.lands_components["F"] = {}
        self.lands_components["M"] = {}
        self.next_set_id["C"] = 1  # Next set ID for cities
        self.next_set_id["R"] = 1  # Next set ID for roads
        self.next_set_id["F"] = 1  # Next set ID for fields
        self.next_set_id["M"] = 1  # Next set ID for monasteries

    def initialize_starting_tile(self) -> None:
        # Define the lands components for each tile type, including the
        # starting tile
        self.add_vertex(
            vertex_id=0, name="CRFR", middle="", orientation=0, position=(0, 0)
        )
        tile = self.tiles_dict["CRFR"]
        for land in tile.tiles_lands.keys():
            for connected in tile.tiles_lands[land]:
                land_id = land + str(self.next_set_id[land])
                self.lands_components[land][land_id] = [(0, connected)]
                self.next_set_id[land] += 1
        # Legacy initialization draft kept for reference:
        # for tile_type, components in tile.items():
        #     for component in components:
        #         set_name = f"{tile_type}{self.next_set_id[tile_type]}"
        #         self.lands_components[tile_type][set_name] = [(0, component)]
        #         self.next_set_id[tile_type] += 1

    def add_vertex(
        self,
        vertex_id: int,
        name: str,
        middle: str,
        orientation: int,
        position: tuple[int, int],
    ) -> None:
        if vertex_id in self.vertices:
            raise ValueError(f"Vertex ID already exists : {vertex_id}")

        if position is None:
            return ValueError("Error in getting position")

        vertex = Vertex(
            id=vertex_id,
            name=name,
            middle=middle,
            tile_dict=self.tiles_dict[name].tiles_lands,
            orientation=orientation % ORIENTATIONS,
            position=position,
        )
        self.vertices[vertex_id] = vertex

        self.turn += 1

        self.compute_neighbors(vertex_id)

    def add_meeple(self, meeple: Meeple) -> None:
        self.meeples.append(meeple)

    def compute_neighbors(self, vertex_id: int) -> None:
        vertex = self.get_vertex(vertex_id)
        if vertex is None:
            raise ValueError(f"Vertex ID not found : {vertex_id}")

        for side in range(ORIENTATIONS):
            potential_neighbor_pos = self.get_position(vertex_id, side)
            for other_vertex in self.vertices.values():
                if other_vertex.get_position() == potential_neighbor_pos:
                    self.set_neighbor(vertex_id, side, other_vertex.get_id())
                    continue

    def set_neighbor(
        self,
        vertex_id: int,
        orientation: int,
        neighbor_id: int,
        bidirectional: bool = True,
    ) -> None:
        if vertex_id not in self.vertices or neighbor_id not in self.vertices:
            raise ValueError("Vertex ID or neighbor ID not found")
        self.vertices[vertex_id].set_neighbor(orientation, neighbor_id)
        if bidirectional:
            opposite_ori = (orientation + (ORIENTATIONS // 2)) % ORIENTATIONS
            self.vertices[neighbor_id].set_neighbor(opposite_ori, vertex_id)

    def remove_vertex(self, vertex_id: int) -> None:
        if vertex_id not in self.vertices:
            raise ValueError(f"Vertex ID not found : {vertex_id}")
        for vertex in self.vertices.values():
            for ori, id in list(vertex.neighbors.items()):
                if id == vertex_id:
                    vertex.remove_neighbor(ori)
                    self.turn -= 1
        del self.vertices[vertex_id]
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

    def remove_meeple(self, tile_id: int, players: dict[int, Player]) -> None:
        for meeple in self.meeples:
            if meeple.tile_id == tile_id:
                self.meeples.remove(meeple)
                meeple_owner = players.get(meeple.player_id)
                meeple_owner.add_meeple()  # Return the meeple to the player
                break

    def get_vertex(self, vertex_id: int) -> Optional[Vertex]:
        return self.vertices.get(vertex_id)

    def get_vertex_id(self, vertex: Vertex) -> int:
        return vertex.get_id()

    def get_verticies(self) -> Dict[int, Vertex]:
        return dict(self.vertices)

    def get_vertices_data(self) -> dict[int, dict]:
        """
        Retourne toutes les informations nécessaires pour l'affichage GUI.
        """
        return {
            vertex_id: {
                "id": vertex.get_id(),
                "x": vertex.get_position()[0],
                "y": vertex.get_position()[1],
                "name": vertex.get_name(),
                "middle": vertex.get_middle(),
                "orientation": vertex.get_orientation(),
            }
            for vertex_id, vertex in self.vertices.items()
        }

    def get_vertice_data(self, vertex: int) -> dict[int, dict]:
        """
        Retourne toutes les informations nécessaires pour l'affichage GUI.
        """
        return {
            self.get_vertex_id(vertex): {
                "id": vertex.get_id(),
                "x": vertex.get_position()[0],
                "y": vertex.get_position()[1],
                "name": vertex.get_name(),
                "middle": vertex.get_middle(),
                "orientation": vertex.get_orientation(),
            }
        }

    def get_position(
        self, vertex_id: int, side: int
    ) -> Optional[tuple[int, int]]:
        vertex = self.get_vertex(vertex_id)
        if vertex is None:
            return None
        x, y = vertex.get_position()
        if side == SOUTH_DIR:
            return (x, y + 1)
        elif side == EAST_DIR:
            return (x + 1, y)
        elif side == NORTH_DIR:
            return (x, y - 1)
        elif side == WEST_DIR:
            return (x - 1, y)
        else:
            raise ValueError(f"Invalid side: {side}")

    def get_position_by_pos(
        self, position: tuple[int, int], side: int
    ) -> Optional[tuple[int, int]]:
        x, y = position
        if side == SOUTH_DIR:
            return (x, y + 1)
        elif side == EAST_DIR:
            return (x + 1, y)
        elif side == NORTH_DIR:
            return (x, y - 1)
        elif side == WEST_DIR:
            return (x - 1, y)
        else:
            raise ValueError(f"Invalid side: {side}")

    def get_neighbors(self, vertex_id: int) -> Dict[int, int]:
        if vertex_id not in self.vertices:
            return {}
        return self.vertices[vertex_id].get_neighbors()

    def get_turn_number(self) -> int:
        return self.turn

    def get_meeples(self) -> List[Meeple]:
        return self.meeples

    def set_meeples(self, meeples_list: List[Meeple]) -> None:
        self.meeples.clear()
        self.meeples.extend(meeples_list)

    def reset_graph(self):
        self.vertices.clear()
        self.lands_components.clear()
        self.next_set_id.clear()
        self.meeples.clear()
        self.turn = 0
        # Resetting the graph with the starting tile (CRFR) as a vertex in the
        # graph
        self.initialize_land_components()
        self.initialize_starting_tile()

    def get_vertex_orientation(self, vertex_id: int) -> int:
        vertex = self.get_vertex(vertex_id)
        if vertex is None:
            raise ValueError(f"Vertex ID not found : {vertex_id}")
        return vertex.get_orientation()

    def find_neighbor_at(
        self, x: int, y: int
    ) -> tuple[Optional[int], Optional[int]]:
        """
        Cherche une tuile voisine autour de (x, y).

        Retourne un tuple (vertex_id, side_relative_to_new_tile)
        side_relative_to_new_tile : côté de la nouvelle tuile où est collé
        le voisin
        """
        # Mapping direction → offset
        neighbors_offset = {
            NORTH_DIR: (0, -1),
            EAST_DIR: (1, 0),
            SOUTH_DIR: (0, 1),
            WEST_DIR: (-1, 0),
        }

        for side, (dx, dy) in neighbors_offset.items():
            nx, ny = x + dx, y + dy
            for vertex in self.vertices.values():
                vx, vy = vertex.get_position()
                if (vx, vy) == (nx, ny):
                    # side représente le côté de la nouvelle tuile où ce voisin
                    # est collé
                    opposite_side = (side + 2) % 4
                    return vertex.get_id(), opposite_side

        return None, None
