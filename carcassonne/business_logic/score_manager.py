import logging
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from carcassonne.i18n import gettext as _
from carcassonne.business_logic.tile_constants import DIRECTION_MAP

if TYPE_CHECKING:
    from carcassonne.business_logic.player import Player

logger = logging.getLogger(__name__)


class ScoreManager:
    def __init__(self):
        """Initialize ScoreManager.

        ScoreManager is a stateless utility class that supports scoring
        calculations for all terrain components (roads, cities, monasteries,
        fields) at both mid-game (end-of-turn) and end-of-game phases.

        Returns:
            None.
        """
        pass

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
            is_complete = ScoreManager._is_monastery_complete(component, graph)
        else:  # Road, City, Stream
            is_complete = ScoreManager._is_edge_component_complete(
                component, graph
            )

        return is_complete

    @staticmethod
    def score_end_of_turn(
        graph,
        players: Dict[int, "Player"],
        current_player_id: int = 0,
        scored_components: set = None,
        emit_logs: bool = True,
        log_events: Optional[list[tuple[str, object]]] = None,
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

        score_fn = {
            "R": ScoreManager._score_road_complete,
            "C": ScoreManager._score_city_complete,
            "M": ScoreManager._score_monastery_complete,
        }

        for terrain in ("R", "C", "M"):
            for name, component in graph.lands_components.get(
                terrain, {}
            ).items():
                key = f"{terrain}:{name}"
                if (
                    key not in scored_components
                    and ScoreManager.is_component_complete(
                        terrain, name, graph
                    )
                ):
                    if log_events is not None:
                        log_events.append(
                            (
                                "component_completed",
                                {
                                    "name": name,
                                    "terrain": terrain,
                                },
                            )
                        )
                    if emit_logs:
                        logger.info(
                            _("Component %s (%s) completed and scored"),
                            name, terrain,
                        )
                    score_fn[terrain](
                        component,
                        name,
                        graph,
                        players,
                    )
                    returned_meeples = (
                        ScoreManager._return_component_meeples_to_players(
                            name, graph, players
                        )
                    )
                    if returned_meeples is None:
                        returned_meeples = {}
                    for player_id, meeple_count in returned_meeples.items():
                        if log_events is not None:
                            log_events.append(
                                (
                                    "meeple_returned",
                                    {
                                        "player_id": player_id,
                                        "count": meeple_count,
                                        "component": name,
                                    },
                                )
                            )
                        if emit_logs:
                            logger.info(
                                _(
                                    "Player %d gets back %d meeple(s)"
                                    " from component %s"
                                ),
                                player_id,
                                meeple_count,
                                name,
                            )
                    scored_components.add(key)

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
        incomplete_fn = {
            "R": ScoreManager._score_road_incomplete,
            "C": ScoreManager._score_city_incomplete,
            "M": ScoreManager._score_monastery_incomplete,
        }

        for terrain, fn in incomplete_fn.items():
            for name, component in graph.lands_components.get(
                terrain, {}
            ).items():
                if not ScoreManager.is_component_complete(
                    terrain, name, graph
                ):
                    fn(component, name, graph, players)

        for name, component in graph.lands_components.get("F", {}).items():
            ScoreManager._score_field(component, name, graph, players)

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

        # Monastery is complete when all 8 surrounding cells are occupied.
        adjacent_count = ScoreManager._count_surrounding_tiles(tile_id, graph)
        is_complete = adjacent_count >= 8
        return is_complete

    @staticmethod
    def _count_surrounding_tiles(tile_id: int, graph) -> int:
        """Count tiles present on the 8 cells surrounding a given tile.

        Used to compute monastery scores, whether complete or not.

        Args:
            tile_id: Identifier of the central tile.
            graph: Current graph state containing all placed vertices.

        Returns:
            Number of occupied neighboring cells (between 0 and 8).
        """
        vertex = graph.vertices.get(tile_id)
        if vertex is None:
            return 0

        x, y = vertex.get_position()
        occupied_positions = {
            v.get_position() for v in graph.vertices.values() if v is not None
        }

        surrounding_positions = {
            (x + dx, y + dy)
            for dx in (-1, 0, 1)
            for dy in (-1, 0, 1)
            if not (dx == 0 and dy == 0)
        }

        return sum(
            1 for pos in surrounding_positions if pos in occupied_positions
        )

    @staticmethod
    def _convert_tile_direction_to_board_direction(
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

        # direction_matrix[orientation][bi][bj] gives the tile-label at board
        # position (bi,bj). We need the inverse lookup: for a raw tile-label
        # direction, find which board cardinal it maps to after rotation.
        board_cardinals = {
            "N": (0, 1),
            "E": (1, 2),
            "S": (2, 1),
            "W": (1, 0),
        }
        matrix = tile_def.direction_matrix[vertex.orientation]
        for board_dir, (bi, bj) in board_cardinals.items():
            if matrix[bi][bj] == raw_direction:
                return board_dir
        return None

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
                oriented_direction = (
                    ScoreManager._convert_tile_direction_to_board_direction(
                        tile_id, direction_str, graph
                    )
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
    def _award_majority_score(
        component_name: str,
        total_points: int,
        graph,
        players: Dict[int, "Player"],
    ) -> None:
        """Award total_points to the player(s) with the most meeples.

        In case of a tie, all tied players receive the full point total.
        Does nothing when no meeple is present on the component.

        Args:
            component_name: Unique component identifier (e.g. `R2`, `C1`).
            total_points: Number of points to award to the winning player(s).
            graph: Current graph state containing the list of placed meeples.
            players: Mapping from player_id to Player instance.

        Returns:
            None. Updates player scores in place.
        """
        meeple_count = ScoreManager.count_meeples_on_component(
            component_name, graph
        )
        if not meeple_count:
            return

        max_count = max(meeple_count.values())
        winners = [
            pid for pid, cnt in meeple_count.items()
            if cnt == max_count and pid in players
        ]
        for player_id in winners:
            players[player_id].get_score().add_score(total_points)

    @staticmethod
    def count_meeples_on_component(
        component_name: str, graph
    ) -> Dict[int, int]:
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
    def count_banners_on_tiles(tile_ids: List[int], graph) -> int:
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
            if vertex and vertex.middle == "b":
                banner_count += 1
        return banner_count

    @staticmethod
    def _return_component_meeples_to_players(
        component_name: str, graph, players: Dict[int, "Player"]
    ) -> Dict[int, int]:
        """Return all meeples placed on a component to their owners.

        This helper is used when a component is completed and has just been
        scored. Meeples on that component are removed from the board and each
        corresponding player's meeple stock is incremented.

        Args:
            component_name: Unique component identifier (for example `C3`).
            graph: Current graph state containing the live meeple list.
            players: Mapping from player id to Player instance.

        Returns:
            Mapping of `player_id -> meeples returned`.
            Also mutates `graph.meeples` and player meeple counts in place.
        """
        remaining_meeples = []
        returned_counts: Dict[int, int] = {}
        for meeple in graph.meeples:
            if meeple.lands_components == component_name:
                owner = players.get(meeple.player_id)
                if owner is not None:
                    owner.add_meeple()
                    returned_counts[meeple.player_id] = (
                        returned_counts.get(meeple.player_id, 0) + 1
                    )
            else:
                remaining_meeples.append(meeple)

        graph.meeples = remaining_meeples
        return returned_counts

    @staticmethod
    def _score_road_complete(
        component: List[Tuple],
        component_name: str,
        graph,
        players: Dict[int, "Player"],
    ) -> None:
        """Apply score for a completed road: 1 point per tile.

        Args:
            component: List of `(tile_id, directions)` tuples for the road.
            component_name: Road component identifier (e.g. `R1`).
            graph: Current graph state.
            players: Mapping from player_id to Player instance.

        Returns:
            None. Updates player scores in place.
        """
        tile_ids = {tid for tid, _ in component}
        ScoreManager._award_majority_score(
            component_name,
            len(tile_ids),
            graph,
            players,
        )

    @staticmethod
    def _score_city_complete(
        component: List[Tuple],
        component_name: str,
        graph,
        players: Dict[int, "Player"],
    ) -> None:
        """Apply score for a completed city: 2 points per tile + 2 per banner.

        Args:
            component: List of `(tile_id, directions)` tuples for the city.
            component_name: City component identifier (e.g. `C2`).
            graph: Current graph state.
            players: Mapping from player_id to Player instance.

        Returns:
            None. Updates player scores in place.
        """
        tile_ids = list({tid for tid, _ in component})
        banners = ScoreManager.count_banners_on_tiles(tile_ids, graph)
        total_points = len(tile_ids) * 2 + banners * 2
        ScoreManager._award_majority_score(
            component_name,
            total_points,
            graph,
            players,
        )

    @staticmethod
    def _score_monastery_complete(
        component: List[Tuple],
        component_name: str,
        graph,
        players: Dict[int, "Player"],
    ) -> None:
        """Apply score for a completed monastery: fixed 9 points.

        Every player with a meeple on the component receives the points
        (no majority rule applies to monasteries).

        Args:
            component: Monastery component data (single tile entry).
            component_name: Monastery component identifier (e.g. `M1`).
            graph: Current graph state.
            players: Mapping from player_id to Player instance.

        Returns:
            None. Updates player scores in place.
        """
        meeple_count = ScoreManager.count_meeples_on_component(
            component_name, graph
        )
        for player_id in meeple_count:
            if player_id in players:
                players[player_id].get_score().add_score(9)

    @staticmethod
    def _score_road_incomplete(
        component: List[Tuple],
        component_name: str,
        graph,
        players: Dict[int, "Player"],
    ) -> None:
        """Apply end-game score for an incomplete road: 1 point per tile.

        Args:
            component: List of `(tile_id, directions)` tuples for the road.
            component_name: Road component identifier (e.g. `R1`).
            graph: Final graph state.
            players: Mapping from player_id to Player instance.

        Returns:
            None. Updates player scores in place.
        """
        tile_ids = {tid for tid, _ in component}
        ScoreManager._award_majority_score(
            component_name, len(tile_ids), graph, players
        )

    @staticmethod
    def _score_city_incomplete(
        component: List[Tuple],
        component_name: str,
        graph,
        players: Dict[int, "Player"],
    ) -> None:
        """Apply end-game score for an incomplete city.

        Rule applied: 1 point per tile + 1 point per banner.

        Args:
            component: List of `(tile_id, directions)` tuples for the city.
            component_name: City component identifier (e.g. `C2`).
            graph: Final graph state.
            players: Mapping from player_id to Player instance.

        Returns:
            None. Updates player scores in place.
        """
        tile_ids = list({tid for tid, _ in component})
        banners = ScoreManager.count_banners_on_tiles(tile_ids, graph)
        total_points = len(tile_ids) + banners
        ScoreManager._award_majority_score(
            component_name, total_points, graph, players
        )

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

        # Monastery scores 1 point for itself + 1 per surrounding tile.
        points = 1 + ScoreManager._count_surrounding_tiles(tile_id, graph)

        meeple_count = ScoreManager.count_meeples_on_component(
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
        ScoreManager._award_majority_score(
            component_name, total_points, graph, players
        )

    @staticmethod
    def _count_adjacent_completed_cities(
        field_component: List[Tuple], graph
    ) -> int:
        """Count unique completed cities adjacent to a field component.

        Builds a reverse lookup (tile_id -> city_name) once to avoid
        rescanning all city components for every neighbouring tile.
        Short-circuits `is_component_complete` for cities already confirmed
        complete in the same call.

        Args:
            field_component: Field component data.
            graph: Final graph state.

        Returns:
            Number of distinct adjacent city components that are complete.
        """
        if "C" not in graph.lands_components:
            return 0

        # Build reverse lookup once: tile_id -> city component name  O(C * T)
        tile_to_city: Dict[int, str] = {
            tile_id: city_name
            for city_name, city_component in graph.lands_components[
                "C"
            ].items()
            for tile_id, _ in city_component
        }

        adjacent_cities: set = set()

        for tile_id, _ in field_component:
            vertex = graph.vertices.get(tile_id)
            if vertex is None:
                continue

            for neighbor_id in vertex.neighbors.values():
                city_name = tile_to_city.get(neighbor_id)
                # Skip if not a city tile, already counted, or city incomplete
                if (
                    city_name is None
                    or city_name in adjacent_cities
                    or not ScoreManager.is_component_complete(
                        "C", city_name, graph
                    )
                ):
                    continue
                adjacent_cities.add(city_name)

        return len(adjacent_cities)
