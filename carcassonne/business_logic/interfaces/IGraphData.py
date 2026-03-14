from abc import ABC, abstractmethod


from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from carcassonne.datas.MeepleData import Meeple

class IGraphData(ABC):
    # pylint: disable=missing-class-docstring
    @abstractmethod
    def add_vertex(self, vertex_id: int, name: str, middle: str, orientation: int, position: tuple[int,int]) -> None:
        pass

    @abstractmethod
    def compute_neighbors(self, vertex_id: int) -> None:
        pass

    @abstractmethod
    def remove_vertex(self, vertex_id: int) -> None:
        pass

    @abstractmethod
    def set_neighbor(self, vertex_id: int, orientation: int, neighbor_id: int, bidirectional: bool = True) -> None:
        pass

    @abstractmethod
    def get_vertex(self, vertex_id: int) -> Optional[Any]:
        pass

    @abstractmethod
    def get_neighbors(self, vertex_id: int) -> Dict[int, int]:
        pass

    @abstractmethod
    def get_turn_number(self) -> int:
        pass

    @abstractmethod
    def get_verticies(self) -> Dict[int, Any]:
        pass

    @abstractmethod
    def get_vertices_data(self) -> dict[int, dict]:
        pass

    @abstractmethod
    def get_vertice_data(self, vertex) -> dict[int, dict]:
        pass

    @abstractmethod
    def get_position(self, vertex_id: int, side: int) -> Optional[tuple[int, int]]:
        pass

    @abstractmethod
    def reset_graph(self):
        pass

    @abstractmethod
    def get_vertex_id(self, vertex) -> int:
        pass

    @abstractmethod
    def get_vertex_orientation(self, vertex_id: int) -> int:
        pass

    @abstractmethod
    def find_neighbor_at(self, x: int, y: int) -> tuple[Optional[int], Optional[int]]:
        pass

    @abstractmethod
    def get_meeples(self) -> List[Meeple]:
        pass
    
    @abstractmethod
    def remove_meeple(self, tile_id: int, players : dict[int, Any]) -> None:
        pass