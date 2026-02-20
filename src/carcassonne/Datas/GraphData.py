"""This module defines the GraphData class, which implements the IGraphData interface to represent the game state of Carcassonne as a graph.
The GraphData class manages the vertices of the graph, which correspond to the tiles placed on the board and their connections.
It provides methods to add and remove vertices, set neighbors, and retrieve vertex information.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional, List

from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData
from carcassonne.Datas.MeepleData import Meeple
from carcassonne.Datas.TilesInfo import TilesInfo
from carcassonne.Datas.TilesInfo import Tile

NORTH_DIR = 0
EAST_DIR = 1
SOUTH_DIR = 2
WEST_DIR = 3

ORIENTATIONS = 4

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

    def __init__(self, id: int, name: str, middle: str, tile_dict: Dict[str, list], orientation: int = 0, position: tuple[int, int] = (0, 0)):
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
            raise ValueError(f"Orientation must be between 0 and {ORIENTATIONS - 1}")
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


class GraphData(IGraphData):
    def __init__(self):
        self.vertices: Dict[int, Vertex] = {}
        self.turn = 0
        # Lands components structure: {land_type: {set_name: [(tile_id, [directions]), ...]}}
        self.lands_components: Dict[str, Dict[str, list]] = {}
        self.next_set_id: Dict[str, int] = {}  # Track next ID per land type
        # List of meeples placed on the board
        self.meeples: List[Meeple] = []
        self.tiles_dict = TilesInfo().tiles
        # Adding the starting tile (CRFR) as a vertex in the graph
        self.initialize_land_components()
        self.initialize_starting_tile()

    def initialize_land_components(self):
        # Initialize land components for the starting tile (CRFR)
        self.lands_components['C'] = {}
        self.lands_components['R'] = {}
        self.lands_components['F'] = {}
        self.lands_components['M'] = {}
        self.next_set_id['C'] = 1  # Next set ID for cities
        self.next_set_id['R'] = 1  # Next set ID for roads
        self.next_set_id['F'] = 1  # Next set ID for fields
        self.next_set_id['M'] = 1  # Next set ID for monasteries
    
    def initialize_starting_tile(self):
        # Define the lands components for each tile type, including the starting tile
        self.add_vertex(vertex_id=0, name='CRFR', middle="", orientation=0, position=(0, 0))
        tile = self.tiles_dict['CRFR']
        print(tile.tiles_lands)
        for land in tile.tiles_lands.keys():
            for connected in tile.tiles_lands[land] :
                land_id = land + str(self.next_set_id[land])
                self.lands_components[land][land_id] = 0, connected
                self.next_set_id[land] += 1
        print(self.lands_components)
        '''
        for type, components in tile.items():
            
            for component in components:
                set_name = f"{type}{self.next_set_id[type]}"
                self.lands_components[type][set_name] = [(0, component)]
                self.next_set_id[type] += 1
        self.lands_components['F'] = {'F1': [(0, ['NE', 'NW'])], 'F2': [(0, ['SE', 'S', 'SW'])]}
        self.lands_components.append({})
        self.next_set_id.append({})'''
    
    def add_vertex(self, vertex_id: int, name: str, middle: str, orientation: int, position: tuple[int,int]) -> None:
        if vertex_id in self.vertices:
            raise ValueError(f"Vertex ID already exists : {vertex_id}")

        if position is None:
            return ValueError("Error in getting position")

        vertex = Vertex(id=vertex_id, name=name, middle=middle, tile_dict=self.tiles_dict[name].tiles_lands, orientation=orientation % ORIENTATIONS, position=position)
        self.vertices[vertex_id] = vertex

        self.turn += 1

        self.compute_neighbors(vertex_id)
        
        self.update_connected_fields(vertex_id)
        
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

    def set_neighbor(self, vertex_id: int, orientation: int, neighbor_id: int, bidirectional: bool = True) -> None:
        if vertex_id not in self.vertices or neighbor_id not in self.vertices:
            raise ValueError(f"Vertex ID or neighbor ID not found")
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

    def get_vertex(self, vertex_id: int) -> Optional[Vertex]:
        return self.vertices.get(vertex_id)

    def get_vertex_id(self, vertex) -> int:
        return vertex.get_id()

    def get_verticies(self) -> Dict[int, Vertex]:
        return dict(self.vertices)

    def get_vertex_orientation(self, vertex_id: int) -> int:
        vertex = self.get_vertex(vertex_id)
        if vertex is None:
            raise ValueError(f"Vertex ID not found : {vertex_id}")
        return vertex.get_orientation()

    def get_position(self, vertex_id: int, side: int) -> Optional[tuple[int, int]]:
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
        
    def get_position_by_pos(self, position: tuple[int, int], side: int) -> Optional[tuple[int, int]]:
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
    
    def update_connected_fields(self, vertex_id: int) -> None:
        tiles_sides_left = ['NW', 'N', 'NE', 'W', 'C', 'E', 'SW', 'S', 'SE']
        neighbors = self.vertices[vertex_id].get_neighbors()
        orientation = self.vertices[vertex_id].get_orientation()
        name = self.vertices[vertex_id].get_name()
        for direction in neighbors.keys():
            field_type = name[(direction - orientation) % 4]
            neighbor_id = neighbors[direction]
        pass

    def reset_graph(self):
        self.vertices.clear()
        self.lands_components.clear()
        self.next_set_id.clear()
        self.meeples.clear()
        self.turn = 0
        # Resetting the graph with the starting tile (CRFR) as a vertex in the graph
        self.add_vertex(vertex_id=0, name='CRFR', middle="", orientation=0, position=(0, 0))
