from collections import deque
from typing import List, Optional, Set
from src.carcassonne.Datas.GraphData import GraphData

class GraphLogic:
    @staticmethod
    def shortest_path(graph: GraphData, start_id: int, end_id: int) -> Optional[List[int]]:
        if start_id not in graph.vertices or end_id not in graph.vertices:
            return None
        queue = deque([[start_id]])
        visited = {start_id}
        while queue:
            path = queue.popleft()
            current = path[-1]
            if current == end_id:
                return path
            for neighbor_id in graph.vertices[current].neighbors.values():
                if neighbor_id not in visited:
                    visited.add(neighbor_id)
                    queue.append(path + [neighbor_id])
        return None

    @staticmethod
    def connected_components(graph: GraphData) -> List[Set[int]]:
        visited: Set[int] = set()
        components: List[Set[int]] = []
        for vertex_id in graph.vertices:
            if vertex_id in visited:
                continue
            comp: Set[int] = set()
            queue = deque([vertex_id])
            while queue:
                current = queue.popleft()
                if current in visited:
                    continue
                visited.add(current)
                comp.add(current)
                for neighbor_id in graph.vertices[current].neighbors.values():
                    if neighbor_id not in visited:
                        queue.append(neighbor_id)
            components.append(comp)
        return components
