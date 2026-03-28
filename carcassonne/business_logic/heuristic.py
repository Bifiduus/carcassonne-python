"""Heuristic module isolated from search algorithms."""

from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True)
class HeuristicWeights:
    """Weights used by the linear evaluation function.

    Each field corresponds to one heuristic feature.
    """

    score_diff: float = 100.0
    meeple_diff: float = 10.0
    latent_score_diff: float = 10.0
    incomplete_city_tiles_diff: float = 1.25
    risky_fields_lt3_diff: float = -40.0


DEFAULT_WEIGHTS = HeuristicWeights()
DEFAULT_COMPRESSION_BIAS = 0.0
# Larger scale makes the sigmoid less sensitive around 0.
DEFAULT_COMPRESSION_SCALE = 250.0
DEFAULT_PLAYER_MEEPLE_STOCK = 7


def _find_player(game_state: Any, player_id: int) -> Any | None:
    """Find a player object by id in the current game state.

    Args:
        game_state: Current game state object.
        player_id: Identifier of the player to search.

    Returns:
        The matching player object, or None if not found.
    """
    for player in game_state.players.values():
        if player.get_id() == player_id:
            return player
    return None


def _get_player_score(game_state: Any, player_id: int) -> float:
    """Read the current score of a player.

    Args:
        game_state: Current game state object.
        player_id: Identifier of the player.

    Returns:
        Player score as float. Returns 0.0 if player is missing.
    """
    player = _find_player(game_state, player_id)
    if player is None:
        return 0.0

    return float(player.get_score().score)


def _get_player_committed_meeples(game_state: Any, player_id: int) -> float:
    """Read how many meeples a player has committed to the board.

    Args:
        game_state: Current game state object.
        player_id: Identifier of the player.

    Returns:
        Number of already-spent meeples as float. Returns 0.0 if the player
        is missing.
    """
    player = _find_player(game_state, player_id)
    if player is None:
        return 0.0

    return float(max(0, DEFAULT_PLAYER_MEEPLE_STOCK - player.meeples))


def _component_meeple_counts(game_state: Any) -> dict[str, dict[int, int]]:
    """Count meeples per land component and per player.

    Args:
        game_state: Current game state object.

    Returns:
        Nested mapping:
        - key level 1: component name (e.g., 'C1', 'R2')
        - key level 2: player id
        - value: number of meeples in that component for that player
    """
    counts: dict[str, dict[int, int]] = {}
    for meeple in game_state.graph.get_meeples():
        component_name = meeple.lands_components
        player_id = meeple.player_id
        if component_name is None:
            continue
        by_player = counts.setdefault(component_name, {})
        by_player[player_id] = by_player.get(player_id, 0) + 1
    return counts


def _component_controllers(
    component_name: str, counts: dict[str, dict[int, int]]
) -> list[int]:
    """Return players controlling a component (majority rule).

    Args:
        component_name: Name of the component to inspect.
        counts: Meeple counts per component/per player.

    Returns:
        List of controlling player ids.
        Multiple ids are returned in case of tie.
    """
    by_player = counts.get(component_name, {})
    if not by_player:
        return []
    max_count = max(by_player.values())
    if max_count <= 0:
        return []
    return [pid for pid, count in by_player.items() if count == max_count]


def _component_tile_count(
    component_entries: list[tuple[int, list[str]]],
) -> float:
    """Count unique tiles present in one component.

    Args:
        component_entries: List of entries (tile_id, directions).

    Returns:
        Number of unique tile ids in the component.
    """
    return float(len({tile_id for tile_id, _ in component_entries}))


def _is_city_component_incomplete(
    graph: Any, entries: list[tuple[int, list[str]]]
) -> bool:
    """Check whether a city component is incomplete.

    A city is considered incomplete if one required cardinal edge has no
    neighbor tile.

    Args:
        graph: Game graph object.
        entries: Component entries for one city component.

    Returns:
        True if the city component is incomplete, False otherwise.
    """
    direction_map = {"N": 0, "E": 1, "S": 2, "W": 3}
    for tile_id, directions in entries:
        vertex = graph.get_vertex(tile_id)
        if vertex is None:
            return True
        neighbors = vertex.get_neighbors()
        for direction in directions:
            if (
                direction in direction_map
                and direction_map[direction] not in neighbors
            ):
                return True
    return False


def _count_incomplete_city_tiles(game_state: Any, player_id: int) -> float:
    """Count tiles of incomplete city components controlled by one player.

    Current approximation:
    - A city component is considered incomplete if at least one edge of one
      involved tile is open (missing neighbor in graph).
    - In case of tied control, tile value is shared equally.

    Args:
        game_state: Current game state object.
        player_id: Identifier of the player to evaluate.

    Returns:
        Estimated number of incomplete city tiles controlled by player_id.
    """
    counts = _component_meeple_counts(game_state)
    total = 0.0
    graph = game_state.graph
    for component_name, entries in graph.lands_components.get("C", {}).items():
        controllers = _component_controllers(component_name, counts)
        if player_id not in controllers:
            continue

        if not _is_city_component_incomplete(graph, entries):
            continue

        share = 1.0 / len(controllers)
        total += share * _component_tile_count(entries)

    return total


def _count_risky_fields_lt3_completed_cities(
    game_state: Any, player_id: int
) -> float:
    """Count controlled field components with fewer than 3 completed cities.

    Current approximation:
    - "Adjacent completed city" is estimated through tile co-presence:
      if a field component and a completed city component share at least one
      tile id, the city is counted as adjacent.
    - In case of tied field control, value is shared equally.

    Args:
        game_state: Current game state object.
        player_id: Identifier of the player to evaluate.

    Returns:
        Estimated number of risky fields for player_id.
    """
    counts = _component_meeple_counts(game_state)
    graph = game_state.graph
    risky_total = 0.0

    completed_city_tile_sets: list[set[int]] = []
    for city_entries in graph.lands_components.get("C", {}).values():
        if _is_city_component_incomplete(graph, city_entries):
            continue
        completed_city_tile_sets.append(
            {tile_id for tile_id, _ in city_entries}
        )

    for field_name, field_entries in graph.lands_components.get(
        "F", {}
    ).items():
        controllers = _component_controllers(field_name, counts)
        if player_id not in controllers:
            continue

        field_tiles = {tile_id for tile_id, _ in field_entries}
        adjacent_completed_cities = sum(
            1
            for city_tiles in completed_city_tile_sets
            if field_tiles & city_tiles
        )

        if adjacent_completed_cities < 3:
            share = 1.0 / len(controllers)
            risky_total += share

    return risky_total


def _estimate_latent_score(game_state: Any, player_id: int) -> float:
    """Estimate latent value for one player from controlled components.

    Current approximation:
    - Uses only C, R, M components.
    - Value is proportional to unique tile count.
    - In case of tied control, value is shared equally.

    Args:
        game_state: Current game state object.
        player_id: Identifier of the player to evaluate.

    Returns:
        Estimated latent score for that player.
    """
    counts = _component_meeple_counts(game_state)
    total = 0.0

    for land_type in ("C", "R", "M"):
        for component_name, entries in game_state.graph.lands_components.get(
            land_type, {}
        ).items():
            controllers = _component_controllers(component_name, counts)
            if player_id not in controllers:
                continue
            share = 1.0 / len(controllers)
            total += share * _component_tile_count(entries)

    return total


def extract_features(
    game_state: Any, player_id: int, opponent_id: int
) -> dict[str, float]:
    """Extract heuristic features as differentials (player - opponent).

    Args:
        game_state: Current game state object.
        player_id: Player being evaluated.
        opponent_id: Opponent player.

    Returns:
        Mapping of feature name to differential value.
    """
    score_diff = _get_player_score(game_state, player_id) - _get_player_score(
        game_state, opponent_id
    )
    meeple_diff = _get_player_committed_meeples(
        game_state, player_id
    ) - _get_player_committed_meeples(game_state, opponent_id)
    latent_score_diff = _estimate_latent_score(
        game_state, player_id
    ) - _estimate_latent_score(game_state, opponent_id)
    incomplete_city_tiles_diff = _count_incomplete_city_tiles(
        game_state, player_id
    ) - _count_incomplete_city_tiles(game_state, opponent_id)
    risky_fields_lt3_diff = _count_risky_fields_lt3_completed_cities(
        game_state, player_id
    ) - _count_risky_fields_lt3_completed_cities(game_state, opponent_id)
    return {
        "score_diff": score_diff,
        "meeple_diff": meeple_diff,
        "latent_score_diff": latent_score_diff,
        "incomplete_city_tiles_diff": incomplete_city_tiles_diff,
        "risky_fields_lt3_diff": risky_fields_lt3_diff,
    }


def _compress_to_star_bounds(
    raw_value: float,
    bias: float = DEFAULT_COMPRESSION_BIAS,
    scale: float = DEFAULT_COMPRESSION_SCALE,
) -> float:
    """Compress a raw heuristic value into [-100, 100] with a sigmoid.

    Args:
        raw_value: Unbounded heuristic value.
        bias: Center used for zero (raw value equal to bias maps to 0).
        scale: Sigmoid scale. Larger scale compresses less aggressively.

    Returns:
        Bounded value in [-100, 100].
    """
    if scale <= 0:
        raise ValueError("Compression scale must be > 0.")

    centered_value = (raw_value - bias) / scale

    # Use a numerically stable sigmoid to avoid overflow on large values.
    if centered_value >= 0:
        exp_term = math.exp(-centered_value)
        win_prob = 1.0 / (1.0 + exp_term)
    else:
        exp_term = math.exp(centered_value)
        win_prob = exp_term / (1.0 + exp_term)

    return float(round((200.0 * win_prob) - 100.0))


def evaluate_state(
    game_state: Any,
    player_id: int,
    opponent_id: int,
    weights: HeuristicWeights = DEFAULT_WEIGHTS,
) -> float:
    """Compute linear heuristic score for a game state.

    Args:
        game_state: Current game state object.
        player_id: Player being evaluated.
        opponent_id: Opponent player.
        weights: Weights applied to each feature.

    Returns:
        Final heuristic value in [-100, 100] (higher is better for player_id).
    """
    features = extract_features(game_state, player_id, opponent_id)
    raw_value = (
        weights.score_diff * features["score_diff"]
        + weights.meeple_diff * features["meeple_diff"]
        + weights.latent_score_diff * features["latent_score_diff"]
        + weights.incomplete_city_tiles_diff
        * features["incomplete_city_tiles_diff"]
        + weights.risky_fields_lt3_diff * features["risky_fields_lt3_diff"]
    )
    return _compress_to_star_bounds(raw_value)
