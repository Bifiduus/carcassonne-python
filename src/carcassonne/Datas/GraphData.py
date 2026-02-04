from typing import Dict, List, Any

class Graph:
    def __init__(self):
        self.adj_list: Dict[Any, List[Any]] = {}

    def add_vertex(self, vertex: Any) -> None:
        if vertex not in self.adj_list:
            self.adj_list[vertex] = []

    def add_edge(self, v1: Any, v2: Any) -> None:
        self.add_vertex(v1)
        self.add_vertex(v2)
        if v2 not in self.adj_list[v1]:
            self.adj_list[v1].append(v2)
        if v1 not in self.adj_list[v2]:
            self.adj_list[v2].append(v1)

    def neighbors(self, vertex: Any) -> List[Any]:
        return self.adj_list.get(vertex, [])
