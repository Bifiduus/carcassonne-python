from dataclasses import dataclass, field
from typing import Dict, Optional

EAST_DIR = 0
SOUTH_DIR = 1
WEST_DIR = 2
NORTH_DIR = 3

ORIENTATIONS = 4

@dataclass
class Vertex:
    id: int
    name: str
    orientation: int = 0
    neighbors: Dict[int, int] = field(default_factory=dict)

    def set_neighbor(self, position: int, neighbor_id: int) -> None:
        if position not in range(ORIENTATIONS):
            raise ValueError(f"Position must be between 0 and {ORIENTATIONS - 1}")
        self.neighbors[position] = neighbor_id

    def remove_neighbor(self, position: int) -> None:
        if position in self.neighbors:
            del self.neighbors[position]

    def rotate(self, k: int = 1) -> None:
        self.orientation = (self.orientation + k) % ORIENTATIONS


class GraphData:
    def __init__(self):
        self.vertices: Dict[int, Vertex] = {}

    def add_vertex(self, vertex_id: int, name: str, orientation: int = 0) -> Vertex:
        if vertex_id in self.vertices:
            raise ValueError(f"Vertex ID already exists : {vertex_id}")
        vertex = Vertex(id=vertex_id, name=name, orientation=orientation % ORIENTATIONS)
        self.vertices[vertex_id] = vertex
        return vertex

    def remove_vertex(self, vertex_id: int) -> None:
        if vertex_id not in self.vertices:
            raise ValueError(f"Vertex ID not found : {vertex_id}")
        for vertex in self.vertices.values():
            for pos, id in list(vertex.neighbors.items()):
                if id == vertex_id:
                    vertex.remove_neighbor(pos)
        del self.vertices[vertex_id]

    def set_neighbor(self, vertex_id: int, position: int, neighbor_id: int, bidirectional: bool = True) -> None:
        if vertex_id not in self.vertices or neighbor_id not in self.vertices:
            raise ValueError(f"Vertex ID or neighbor ID not found")
        self.vertices[vertex_id].set_neighbor(position, neighbor_id)
        if bidirectional:
            opposite_pos = (position + (ORIENTATIONS // 2)) % ORIENTATIONS
            self.vertices[neighbor_id].set_neighbor(opposite_pos, vertex_id)

    def get_vertex(self, vertex_id: int) -> Optional[Vertex]:
        return self.vertices.get(vertex_id)

    def get_neighbors(self, vertex_id: int) -> Dict[int, int]:
        if vertex_id not in self.vertices:
            return {}
        return dict(self.vertices[vertex_id].neighbors)