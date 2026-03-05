from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from carcassonne.Datas.GraphData import NORTH_DIR, EAST_DIR, SOUTH_DIR, WEST_DIR

if TYPE_CHECKING:
    from carcassonne.BusinessLogic.Player import Player

# Mapping between position strings and cardinal directions
DIRECTION_MAP = {
    'N': NORTH_DIR,   # 0
    'E': EAST_DIR,    # 1
    'S': SOUTH_DIR,   # 2
    'W': WEST_DIR     # 3
}


class PlayerScore():
    id: int
    score: int

    def __init__(self, id: int):
        self.id = id
        self.score = 0

    def add_score(self, score: int) -> None:
        self.score += score

    def setPoints(self, points: int) -> None:
        self.score = points

class ScoreManager():
    def __init__(self):
        pass

    @staticmethod
    def is_component_complete(terrain_type: str, component_name: str, graph) -> bool:
        """Check if a terrain component is complete (can't expand).

        For Road/City/Stream: complete if no adjacent empty space
        For Monastery: complete if surrounded by 8 tiles
        """
        if terrain_type not in graph.lands_components:
            return False

        if component_name not in graph.lands_components[terrain_type]:
            return False

        component = graph.lands_components[terrain_type][component_name]

        if terrain_type == 'M':  # Monastery
            return ScoreManager._is_monastery_complete(component, graph)
        else:  # Road, City, Stream
            return ScoreManager._is_edge_component_complete(component, graph)

    @staticmethod
    def _is_monastery_complete(component: List[Tuple], graph) -> bool:
        """A monastery is complete when it has 8 adjacent tiles."""
        if not component or len(component) == 0:
            return False

        tile_id, _ = component[0]  # Monastery has only one tile
        vertex = graph.vertices.get(tile_id)
        if vertex is None:
            return False

        # Count adjacent tiles (should be exactly 8 for complete monastery)
        adjacent_count = len(vertex.neighbors)
        return adjacent_count >= 8

    @staticmethod
    def _is_edge_component_complete(component: List[Tuple], graph) -> bool:
        """A Road/City/Stream is complete when it has no free edges.

        A free edge is a direction in the component that doesn't have
        a neighbor in that direction, meaning the component can potentially expand.
        """
        if not component:
            return False

        # Collect all tile IDs in the component for fast lookup
        component_tile_ids = set(tile_id for tile_id, _ in component)

        # For each tile in the component, check each cardinal direction
        for tile_id, directions_list in component:
            vertex = graph.vertices.get(tile_id)
            if vertex is None:
                continue

            # Check each cardinal direction in this tile's directions
            for direction_str in directions_list:
                # Skip non-cardinal directions (corners and center)
                if direction_str not in ['N', 'E', 'S', 'W']:
                    continue

                direction_int = DIRECTION_MAP.get(direction_str)
                if direction_int is None:
                    continue

                # Check if there's a neighbor in this direction
                has_neighbor_in_direction = direction_int in vertex.neighbors

                if not has_neighbor_in_direction:
                    # This is a free edge - component can expand here
                    return False

                # If there is a neighbor, check if it's in the component
                neighbor_id = vertex.neighbors[direction_int]
                if neighbor_id not in component_tile_ids:
                    # Neighbor exists but is not in this component - free edge
                    return False

        # No free edges found - component is complete
        return True

    @staticmethod
    def score_end_of_turn(graph, players: Dict[int, 'Player']) -> None:
        """Score at end of turn for completed Road, City, and Monastery components."""
        # Score Roads
        if 'R' in graph.lands_components:
            for road_name, road_component in graph.lands_components['R'].items():
                if ScoreManager.is_component_complete('R', road_name, graph):
                    ScoreManager._score_road_complete(road_component, road_name, graph, players)

        # Score Cities
        if 'C' in graph.lands_components:
            for city_name, city_component in graph.lands_components['C'].items():
                if ScoreManager.is_component_complete('C', city_name, graph):
                    ScoreManager._score_city_complete(city_component, city_name, graph, players)

        # Score Monasteries
        if 'M' in graph.lands_components:
            for monastery_name, monastery_component in graph.lands_components['M'].items():
                if ScoreManager.is_component_complete('M', monastery_name, graph):
                    ScoreManager._score_monastery_complete(monastery_component, monastery_name, graph, players)

    @staticmethod
    def _score_road_complete(component: List[Tuple], component_name: str, graph, players: Dict[int, 'Player']) -> None:
        """TODO"""
        return

    @staticmethod
    def _score_city_complete(component: List[Tuple], component_name: str, graph, players: Dict[int, 'Player']) -> None:
        """TODO"""
        return

    @staticmethod
    def _score_monastery_complete(component: List[Tuple], component_name: str, graph, players: Dict[int, 'Player']) -> None:
        """TODO"""
        return

    @staticmethod
    def score_end_of_game(graph, players: Dict[int, 'Player']) -> None:
        """Score at end of game for non-completed R, C, M and all Fields."""
        # Score incomplete Roads
        if 'R' in graph.lands_components:
            for road_name, road_component in graph.lands_components['R'].items():
                if not ScoreManager.is_component_complete('R', road_name, graph):
                    ScoreManager._score_road_incomplete(road_component, road_name, graph, players)

        # Score incomplete Cities
        if 'C' in graph.lands_components:
            for city_name, city_component in graph.lands_components['C'].items():
                if not ScoreManager.is_component_complete('C', city_name, graph):
                    ScoreManager._score_city_incomplete(city_component, city_name, graph, players)

        # Score incomplete Monasteries
        if 'M' in graph.lands_components:
            for monastery_name, monastery_component in graph.lands_components['M'].items():
                if not ScoreManager.is_component_complete('M', monastery_name, graph):
                    ScoreManager._score_monastery_incomplete(monastery_component, monastery_name, graph, players)

        # Score Fields
        if 'F' in graph.lands_components:
            for field_name, field_component in graph.lands_components['F'].items():
                ScoreManager._score_field(field_component, field_name, graph, players)

    @staticmethod
    def _score_road_incomplete(component: List[Tuple], component_name: str, graph, players: Dict[int, 'Player']) -> None:
        """TODO"""
        return

    @staticmethod
    def _score_city_incomplete(component: List[Tuple], component_name: str, graph, players: Dict[int, 'Player']) -> None:
        """TODO"""
        return

    @staticmethod
    def _score_monastery_incomplete(component: List[Tuple], component_name: str, graph, players: Dict[int, 'Player']) -> None:
        """TODO"""
        return

    @staticmethod
    def _score_field(component: List[Tuple], component_name: str, graph, players: Dict[int, 'Player']) -> None:
        """TODO"""
        return


class EndGameScore():

    players_score: list[PlayerScore]

    def __init__(self, players_score: list[PlayerScore]):
        self.players_score = players_score

    def add_final_scores(self) -> None:
        for player_score in self.players_score:
            #TODO
            pass
