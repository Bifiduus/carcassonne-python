from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from carcassonne.business_logic.player import Player

# Direction constants
NORTH_DIR = 0
EAST_DIR = 1
SOUTH_DIR = 2
WEST_DIR = 3

# Mapping between position strings and cardinal directions
DIRECTION_MAP = {
    "N": NORTH_DIR,  # 0
    "E": EAST_DIR,  # 1
    "S": SOUTH_DIR,  # 2
    "W": WEST_DIR,  # 3
}


class PlayerScore:
    id: int
    score: int

    def __init__(self, id: int):
        self.id = id
        self.score = 0

    def add_score(self, score: int) -> None:
        self.score += score

    def set_points(self, points: int) -> None:
        self.score = points


class ScoreManager:
    def __init__(self):
        pass

    @staticmethod
    def _return_component_meeples(
        component_name: str, graph, players: Dict[int, "Player"]
    ) -> None:
        """Return all meeples placed on a component to their owners.

        This helper is used when a component is completed and has just been
        scored. Meeples on that component are removed from the board and each
        corresponding player's meeple stock is incremented.

        Args:
            component_name: Unique component identifier (for example `C3`).
            graph: Current graph state containing the live meeple list.
            players: Mapping from player id to Player instance.

        Returns:
            None. Mutates `graph.meeples` and player meeple counts in place.
        """
        remaining_meeples = []
        for meeple in graph.meeples:
            if meeple.lands_components == component_name:
                owner = players.get(meeple.player_id)
                if owner is not None:
                    owner.add_meeple()
            else:
                remaining_meeples.append(meeple)

        graph.meeples = remaining_meeples

    @staticmethod
    def _to_oriented_cardinal(
        tile_id: int, raw_direction: str, graph
    ) -> Optional[str]:
        """Convert an unrotated direction to board-oriented cardinal.

        Component directions are stored from the base tile definition. This
        method maps them to the effective board orientation according to the
        tile rotation already placed in the graph.

        Args:
            tile_id: Identifier of the tile in the graph.
            raw_direction: Original direction from the tile definition
                (`N`, `E`, `S`, `W`).
            graph: Graph state containing vertices and tile definitions.

        Returns:
            A cardinal direction (`N`, `E`, `S`, `W`) after orientation, or
            None if conversion cannot be performed.
        """
        if raw_direction not in ["N", "E", "S", "W"]:
            return None

        vertex = graph.vertices.get(tile_id)
        if vertex is None:
            return None

        tile_code = vertex.name.split("/")[0]
        tile_def = graph.tiles_dict.get(tile_code)
        if tile_def is None:
            return raw_direction

        i, j = {"N": (0, 1), "E": (1, 2), "S": (2, 1), "W": (1, 0)}[
            raw_direction
        ]
        oriented = tile_def.direction_matrix[vertex.orientation][i][j]
        return oriented if oriented in ["N", "E", "S", "W"] else None

    @staticmethod
    def is_component_complete(
        terrain_type: str, component_name: str, graph
    ) -> bool:
        """Tell whether a terrain component is complete.

        Completion means the component cannot legally expand anymore.
        Monasteries and edge-based terrains use different completion checks.

        Args:
            terrain_type: Terrain key (`R`, `C`, `M`, etc.).
            component_name: Identifier of the component inside
                `graph.lands_components[terrain_type]`.
            graph: Current graph state.

        Returns:
            True if the component is complete, otherwise False.
        """
        if terrain_type not in graph.lands_components:
            return False

        if component_name not in graph.lands_components[terrain_type]:
            return False

        component = graph.lands_components[terrain_type][component_name]

        if terrain_type == "M":  # Monastery
            return ScoreManager._is_monastery_complete(component, graph)
        else:  # Road, City, Stream
            return ScoreManager._is_edge_component_complete(component, graph)

    @staticmethod
    def _is_monastery_complete(component: List[Tuple], graph) -> bool:
        """Check monastery completion by adjacency count.

        Args:
            component: Monastery component representation (single tile entry).
            graph: Current graph state.

        Returns:
            True when the monastery is surrounded by 8 neighboring tiles,
            otherwise False.
        """
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
        """Check completion for edge-based terrains (Road/City/Stream).

        The component is complete when none of its cardinal edges can expand.

        Args:
            component: List of tuples `(tile_id, directions)` describing the
                tiles and edge directions that belong to the component.
            graph: Current graph state.

        Returns:
            True if there is no free edge, otherwise False.
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
                if direction_str not in ["N", "E", "S", "W"]:
                    continue

                # Component directions are from base tile definitions.
                # Convert to board-oriented directions first.
                oriented_direction = ScoreManager._to_oriented_cardinal(
                    tile_id, direction_str, graph
                )
                if oriented_direction is None:
                    continue

                direction_int = DIRECTION_MAP.get(oriented_direction)
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
    def get_meeples_on_component(component_name: str, graph) -> Dict[int, int]:
        """Count meeples placed on a component, grouped by player.

        Args:
            component_name: Unique component identifier.
            graph: Current graph state containing all placed meeples.

        Returns:
            Dictionary mapping `player_id -> meeple_count` for the component.
            Returns an empty dict when no meeple is present.
        """
        meeple_count = {}

        for meeple in graph.meeples:
            if meeple.lands_components == component_name:
                if meeple.player_id not in meeple_count:
                    meeple_count[meeple.player_id] = 0
                meeple_count[meeple.player_id] += 1

        return meeple_count

    @staticmethod
    def get_banners_on_tiles(tile_ids: List[int], graph) -> int:
        """Count banner symbols across a list of city tiles.

        Args:
            tile_ids: Tile identifiers to inspect.
            graph: Current graph state with tile vertices.

        Returns:
            Number of banners found.
        """
        banner_count = 0
        for tile_id in tile_ids:
            vertex = graph.vertices.get(tile_id)
            if vertex and "/b" in vertex.name:
                banner_count += 1
        return banner_count

    @staticmethod
    def score_end_of_turn(
        graph,
        players: Dict[int, "Player"],
        current_player_id: int = 0,
        scored_components: set = None,
    ) -> None:
        """Score components completed by the latest placement.

        Completed Roads, Cities and Monasteries are scored once, then all
        meeples on those components are returned to their owners.

        Args:
            graph: Current graph state.
            players: Mapping from player id to Player instance.
            current_player_id: Kept for compatibility with existing call sites.
            scored_components: Mutable set of already-scored component keys.

        Returns:
            None. Mutates player scores, meeple pools and scored component set.
        """
        if scored_components is None:
            scored_components = set()

        # Score Roads
        if "R" in graph.lands_components:
            for road_name, road_component in graph.lands_components[
                "R"
            ].items():
                component_key = f"R:{road_name}"
                is_complete = ScoreManager.is_component_complete(
                    "R", road_name, graph
                )
                if component_key not in scored_components and is_complete:
                    ScoreManager._score_road_complete(
                        road_component,
                        road_name,
                        graph,
                        players,
                        current_player_id,
                    )
                    ScoreManager._return_component_meeples(
                        road_name, graph, players
                    )
                    scored_components.add(component_key)

        # Score Cities
        if "C" in graph.lands_components:
            for city_name, city_component in graph.lands_components[
                "C"
            ].items():
                component_key = f"C:{city_name}"
                is_complete = ScoreManager.is_component_complete(
                    "C", city_name, graph
                )
                if component_key not in scored_components and is_complete:
                    ScoreManager._score_city_complete(
                        city_component,
                        city_name,
                        graph,
                        players,
                        current_player_id,
                    )
                    ScoreManager._return_component_meeples(
                        city_name, graph, players
                    )
                    scored_components.add(component_key)

        # Score Monasteries
        if "M" in graph.lands_components:
            for monastery_name, monastery_component in graph.lands_components[
                "M"
            ].items():
                component_key = f"M:{monastery_name}"
                is_complete = ScoreManager.is_component_complete(
                    "M", monastery_name, graph
                )
                if component_key not in scored_components and is_complete:
                    ScoreManager._score_monastery_complete(
                        monastery_component,
                        monastery_name,
                        graph,
                        players,
                        current_player_id,
                    )
                    ScoreManager._return_component_meeples(
                        monastery_name, graph, players
                    )
                    scored_components.add(component_key)

    @staticmethod
    def _score_road_complete(
        component: List[Tuple],
        component_name: str,
        graph,
        players: Dict[int, "Player"],
        current_player_id: int = 0,
    ) -> None:
        """Apply score for a completed road.

        Rule applied: 1 point per tile in the road, only if at least one
        meeple is present. In case of majority tie, all tied players score.

        Args:
            component: Road component data.
            component_name: Road component identifier.
            graph: Current graph state.
            players: Mapping from player id to Player instance.
            current_player_id: Unused compatibility parameter.

        Returns:
            None. Updates player scores in place.
        """
        tile_ids = [tid for tid, _ in component]
        points_per_tile = 1
        total_points = len(tile_ids) * points_per_tile

        meeple_count = ScoreManager.get_meeples_on_component(
            component_name, graph
        )
        if not meeple_count:
            return

        max_count = max(meeple_count.values())
        winning_players = [
            player_id
            for player_id, count in meeple_count.items()
            if count == max_count
        ]

        for player_id in winning_players:
            if player_id in players:
                players[player_id].get_score().add_score(total_points)

    @staticmethod
    def _score_city_complete(
        component: List[Tuple],
        component_name: str,
        graph,
        players: Dict[int, "Player"],
        current_player_id: int = 0,
    ) -> None:
        """Apply score for a completed city.

        Rule applied: 2 points per tile plus 2 points per banner, only if at
        least one meeple is present. In case of majority tie, all tied players
        score the full amount.

        Args:
            component: City component data.
            component_name: City component identifier.
            graph: Current graph state.
            players: Mapping from player id to Player instance.
            current_player_id: Unused compatibility parameter.

        Returns:
            None. Updates player scores in place.
        """
        tile_ids = [tid for tid, _ in component]
        points_per_tile = 2
        points_per_banner = 2

        banners = ScoreManager.get_banners_on_tiles(tile_ids, graph)
        total_points = (len(tile_ids) * points_per_tile) + (
            banners * points_per_banner
        )

        meeple_count = ScoreManager.get_meeples_on_component(
            component_name, graph
        )
        if not meeple_count:
            return

        max_count = max(meeple_count.values())
        winning_players = [
            player_id
            for player_id, count in meeple_count.items()
            if count == max_count
        ]

        for player_id in winning_players:
            if player_id in players:
                players[player_id].get_score().add_score(total_points)

    @staticmethod
    def _score_monastery_complete(
        component: List[Tuple],
        component_name: str,
        graph,
        players: Dict[int, "Player"],
        current_player_id: int = 0,
    ) -> None:
        """Apply score for a completed monastery.

        Rule applied: fixed 9 points when at least one meeple is present on the
        monastery component.

        Args:
            component: Monastery component data.
            component_name: Monastery component identifier.
            graph: Current graph state.
            players: Mapping from player id to Player instance.
            current_player_id: Unused compatibility parameter.

        Returns:
            None. Updates player scores in place.
        """
        points = 9

        meeple_count = ScoreManager.get_meeples_on_component(
            component_name, graph
        )
        if not meeple_count:
            return

        for player_id in meeple_count.keys():
            if player_id in players:
                players[player_id].get_score().add_score(points)

    @staticmethod
    def score_end_of_game(graph, players: Dict[int, "Player"]) -> None:
        """Apply all end-of-game scoring rules.

        Scores incomplete Roads/Cities/Monasteries and all Fields according to
        current game rules.

        Args:
            graph: Final graph state when the game ends.
            players: Mapping from player id to Player instance.

        Returns:
            None. Updates player scores in place.
        """
        # Score incomplete Roads
        if "R" in graph.lands_components:
            for road_name, road_component in graph.lands_components[
                "R"
            ].items():
                if not ScoreManager.is_component_complete(
                    "R", road_name, graph
                ):
                    ScoreManager._score_road_incomplete(
                        road_component, road_name, graph, players
                    )

        # Score incomplete Cities
        if "C" in graph.lands_components:
            for city_name, city_component in graph.lands_components[
                "C"
            ].items():
                if not ScoreManager.is_component_complete(
                    "C", city_name, graph
                ):
                    ScoreManager._score_city_incomplete(
                        city_component, city_name, graph, players
                    )

        # Score incomplete Monasteries
        if "M" in graph.lands_components:
            for monastery_name, monastery_component in graph.lands_components[
                "M"
            ].items():
                if not ScoreManager.is_component_complete(
                    "M", monastery_name, graph
                ):
                    ScoreManager._score_monastery_incomplete(
                        monastery_component, monastery_name, graph, players
                    )

        # Score Fields
        if "F" in graph.lands_components:
            for field_name, field_component in graph.lands_components[
                "F"
            ].items():
                ScoreManager._score_field(
                    field_component, field_name, graph, players
                )

    @staticmethod
    def _score_road_incomplete(
        component: List[Tuple],
        component_name: str,
        graph,
        players: Dict[int, "Player"],
    ) -> None:
        """Apply end-game score for an incomplete road.

        Rule applied: 1 point per tile, only if at least one meeple is present.
        In case of majority tie, all tied players score.

        Args:
            component: Road component data.
            component_name: Road component identifier.
            graph: Final graph state.
            players: Mapping from player id to Player instance.

        Returns:
            None. Updates player scores in place.
        """
        tile_ids = [tid for tid, _ in component]
        points_per_tile = 1
        total_points = len(tile_ids) * points_per_tile

        meeple_count = ScoreManager.get_meeples_on_component(
            component_name, graph
        )
        if not meeple_count:
            return

        max_count = max(meeple_count.values())
        winning_players = [
            player_id
            for player_id, count in meeple_count.items()
            if count == max_count
        ]

        for player_id in winning_players:
            if player_id in players:
                players[player_id].get_score().add_score(total_points)

    @staticmethod
    def _score_city_incomplete(
        component: List[Tuple],
        component_name: str,
        graph,
        players: Dict[int, "Player"],
    ) -> None:
        """Apply end-game score for an incomplete city.

        Rule applied: 1 point per tile plus 1 point per banner, only if at
        least one meeple is present. In case of majority tie, all tied players
        score the full amount.

        Args:
            component: City component data.
            component_name: City component identifier.
            graph: Final graph state.
            players: Mapping from player id to Player instance.

        Returns:
            None. Updates player scores in place.
        """
        tile_ids = [tid for tid, _ in component]
        points_per_tile = 1
        points_per_banner = 1

        banners = ScoreManager.get_banners_on_tiles(tile_ids, graph)
        total_points = (len(tile_ids) * points_per_tile) + (
            banners * points_per_banner
        )

        meeple_count = ScoreManager.get_meeples_on_component(
            component_name, graph
        )
        if not meeple_count:
            return

        max_count = max(meeple_count.values())
        winning_players = [
            player_id
            for player_id, count in meeple_count.items()
            if count == max_count
        ]

        for player_id in winning_players:
            if player_id in players:
                players[player_id].get_score().add_score(total_points)

    @staticmethod
    def _score_monastery_incomplete(
        component: List[Tuple],
        component_name: str,
        graph,
        players: Dict[int, "Player"],
    ) -> None:
        """Apply end-game score for an incomplete monastery.

        Points are awarded only when there is exactly one meeple on the
        monastery component.

        Args:
            component: Monastery component data.
            component_name: Monastery component identifier.
            graph: Final graph state.
            players: Mapping from player id to Player instance.

        Returns:
            None. Updates player scores in place.
        """
        if not component:
            return

        tile_id, _ = component[0]
        vertex = graph.vertices.get(tile_id)
        if vertex is None:
            return

        # Monastery scores 1 point for itself + 1 per adjacent tile.
        points = 1 + len(vertex.neighbors)

        meeple_count = ScoreManager.get_meeples_on_component(
            component_name, graph
        )
        total_meeples = sum(meeple_count.values())
        if total_meeples != 1:
            return

        owner_id = next(iter(meeple_count.keys()))
        if owner_id in players:
            players[owner_id].get_score().add_score(points)

    @staticmethod
    def _score_field(
        component: List[Tuple],
        component_name: str,
        graph,
        players: Dict[int, "Player"],
    ) -> None:
        """Apply end-game score for a field component.

        Rule applied: 3 points per adjacent completed city, only if at least
        one meeple is present. In case of majority tie, all tied players score.

        Args:
            component: Field component data.
            component_name: Field component identifier.
            graph: Final graph state.
            players: Mapping from player id to Player instance.

        Returns:
            None. Updates player scores in place.
        """
        points_per_adjacent_city = 3

        # Count adjacent completed cities
        adjacent_completed_cities = (
            ScoreManager._count_adjacent_completed_cities(component, graph)
        )

        total_points = adjacent_completed_cities * points_per_adjacent_city

        meeple_count = ScoreManager.get_meeples_on_component(
            component_name, graph
        )
        if not meeple_count:
            return

        max_count = max(meeple_count.values())
        winning_players = [
            player_id
            for player_id, count in meeple_count.items()
            if count == max_count
        ]

        for player_id in winning_players:
            if player_id in players:
                players[player_id].get_score().add_score(total_points)

    @staticmethod
    def _count_adjacent_completed_cities(
        field_component: List[Tuple], graph
    ) -> int:
        """Count unique completed cities adjacent to a field component.

        Args:
            field_component: Field component data.
            graph: Final graph state.

        Returns:
            Number of distinct adjacent city components that are complete.
        """
        adjacent_cities = set()

        # For each tile in the field
        for tile_id, _ in field_component:
            vertex = graph.vertices.get(tile_id)
            if vertex is None:
                continue

            # Check all adjacent tiles (neighbors)
            for neighbor_id in vertex.neighbors.values():
                neighbor_vertex = graph.vertices.get(neighbor_id)
                if neighbor_vertex is None:
                    continue

                # Find which city component this neighbor belongs to
                city_name = ScoreManager._find_city_component_for_tile(
                    neighbor_id, graph
                )

                # If it's part of a city and the city is complete, count it
                if city_name and ScoreManager.is_component_complete(
                    "C", city_name, graph
                ):
                    adjacent_cities.add(city_name)

        return len(adjacent_cities)

    @staticmethod
    def _find_city_component_for_tile(tile_id: int, graph) -> Optional[str]:
        """Find which city component contains a given tile.

        Args:
            tile_id: Tile identifier to search.
            graph: Graph state containing city component partitions.

        Returns:
            City component name (for example `C1`) if found, otherwise None.
        """
        if "C" not in graph.lands_components:
            return None

        for city_name, city_component in graph.lands_components["C"].items():
            for component_tile_id, _ in city_component:
                if component_tile_id == tile_id:
                    return city_name

        return None


class EndGameScore:

    players_score: list[PlayerScore]

    def __init__(self, players_score: list[PlayerScore]):
        self.players_score = players_score

    def add_final_scores(self) -> None:
        for player_score in self.players_score:
            # TODO
            pass
