from dataclasses import dataclass, field
from typing import Dict, Optional

NORTH_DIR = 0
EAST_DIR = 1
SOUTH_DIR = 2
WEST_DIR = 3

ORIENTATIONS = 4

@dataclass
class Vertex:
    id: int
    name: str
    orientation: int = 0
    neighbors: Dict[int, int] = field(default_factory=dict)
    
    def __init__(self, id: int, name: str, orientation: int = 0):
        self.id = id
        self.name = name
        self.orientation = orientation % ORIENTATIONS
        self.neighbors = {} 

    def set_neighbor(self, position: int, neighbor_id: int) -> None:
        if position not in range(ORIENTATIONS):
            raise ValueError(f"Position must be between 0 and {ORIENTATIONS - 1}")
        self.neighbors[position] = neighbor_id

    def remove_neighbor(self, position: int) -> None:
        if position in self.neighbors:
            del self.neighbors[position]

    def rotate(self, k: int = 1) -> None:
        self.orientation = (self.orientation + k) % ORIENTATIONS
        
    def get_id(self) -> int:
        return self.id
    
    def get_name(self) -> str:  
        return self.name
    
    def get_orientation(self) -> int:
        return self.orientation
    
    def get_neighbors(self) -> Dict[int, int]:
        return dict(self.neighbors)
    
    def is_neighbor_free(self, position: int) -> bool:
        return position not in self.neighbors


class GraphData:
    def __init__(self):
        self.vertices: Dict[int, Vertex] = {}
        self.turn = 0
        self.add_vertex(vertex_id=0, name='CRFR', orientation=0)  # Adding the starting tile (CRFR) as a vertex in the graph

    def add_vertex(self, vertex_id: int, name: str, orientation: int):
        if vertex_id in self.vertices:
            raise ValueError(f"Vertex ID already exists : {vertex_id}")
        vertex = Vertex(id=vertex_id, name=name, orientation=orientation % ORIENTATIONS)
        self.vertices[vertex_id] = vertex
        self.turn += 1

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
        return self.vertices[vertex_id].get_neighbors()
    
    def get_turn_number(self) -> int:
        return self.turn    
    
    def get_verticies(self) -> Dict[int, Vertex]:
        return dict(self.vertices)  