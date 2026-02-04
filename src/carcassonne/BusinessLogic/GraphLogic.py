from collections import deque
from typing import Any, List, Optional, Set
from src.carcassonne.Datas.GraphData import Graph

class GraphLogic:
    @staticmethod
    def shortest_path(graph: Graph, start: Any, end: Any) -> Optional[List[Any]]:
        if start not in graph.adj_list or end not in graph.adj_list:
            return None
        queue = deque([[start]])
        visited = set([start])
        while queue:
            path = queue.popleft()
            node = path[-1]
            if node == end:
                return path
            for neighbor in graph.neighbors(node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])
        return None

    @staticmethod
    def connected_components(graph: Graph) -> List[Set[Any]]:
        visited = set()
        components = []
        for vertex in graph.adj_list:
            if vertex not in visited:
                comp = set()
                queue = deque([vertex])
                while queue:
                    v = queue.popleft()
                    if v not in visited:
                        visited.add(v)
                        comp.add(v)
                        queue.extend([n for n in graph.neighbors(v) if n not in visited])
                components.append(comp)
        return components
