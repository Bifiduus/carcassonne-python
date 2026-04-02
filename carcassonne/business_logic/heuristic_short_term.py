"""Short-term tactical heuristic isolated from search algorithms.

This heuristic focuses on near-term score swings rather than long-term board
value. It estimates which player is more likely to score and recover meeples
soon from Roads, Cities, and Monasteries.
"""

from dataclasses import dataclass
import math
from typing import Any

from carcassonne.business_logic.score_manager import (
    DIRECTION_MAP,
    ScoreManager,
)


@dataclass(frozen=True)
class ShortTermWeights:
    """Weights used by the short-term tactical evaluation.

    Each field corresponds to one short-term tactical feature.
    """

    score_diff: float = 35.0
    available_meeples_diff: float = 8.0
    imminent_points_diff: float = 28.0
    imminent_meeple_returns_diff: float = 18.0
    ready_components_diff: float = 12.0
    pressure_components_diff: float = 5.0


DEFAULT_WEIGHTS = ShortTermWeights()
DEFAULT_COMPRESSION_BIAS = 0.0
# Larger scale makes the sigmoid less sensitive around 0.
DEFAULT_COMPRESSION_SCALE = 250.0
CARDINAL_DIRECTIONS = {"N", "E", "S", "W"}


def _find_player(game_state: Any, player_id: int) -> Any | None:
    """Find a player object by id in the current game state.

    Args:
        game_state: Current game state object.
        player_id: Identifier of the player to search.

    Returns:
        The matching player object, or None if not found.
    """
    for player in game_state.game_data.players.values():
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


def _get_player_meeples(game_state: Any, player_id: int) -> float:
    """Read the number of available meeples for a player.

    Args:
        game_state: Current game state object.
        player_id: Identifier of the player.

    Returns:
        Number of available meeples as float. Returns 0.0 if player is
        missing.
    """
    player = _find_player(game_state, player_id)
    if player is None:
        return 0.0
    return float(player.get_meeples())


def _component_meeple_counts(game_state: Any) -> dict[str, dict[int, int]]:
    """Count meeples per land component and per player.

    Args:
        game_state: Current game state object.

    Returns:
        Nested mapping:
        - key level 1: component name (e.g., ``"C1"``, ``"R2"``)
        - key level 2: player id
        - value: number of meeples in that component for that player
    """
    counts: dict[str, dict[int, int]] = {}
    for meeple in game_state.game_data.graph.get_meeples():
        component_name = meeple.lands_components
        if component_name is None:
            continue
        by_player = counts.setdefault(component_name, {})
        by_player[meeple.player_id] = by_player.get(meeple.player_id, 0) + 1
    return counts


def _component_controllers(
    component_name: str, counts: dict[str, dict[int, int]]
) -> list[int]:
    """Return players controlling a component under majority rule.

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
        component_entries: List of entries ``(tile_id, directions)``.

    Returns:
        Number of unique tile ids in the component.
    """
    return float(len({tile_id for tile_id, _ in component_entries}))


def _estimate_completion_points(
    land_type: str, component_entries: list[tuple[int, list[str]]], graph: Any
) -> float:
    """Estimate points earned if this component is completed soon.

    Current approximation:
    - Roads score 1 point per unique tile.
    - Cities score 2 points per unique tile plus 2 per banner.
    - Monasteries always score 9 when completed.

    Args:
        land_type: Type of component (``"R"``, ``"C"``, ``"M"``).
        component_entries: Entries describing the component.
        graph: Game graph object.

    Returns:
        Estimated completion score for this component.
    """
    if land_type == "R":
        return _component_tile_count(component_entries)
    if land_type == "C":
        tile_ids = list({tile_id for tile_id, _ in component_entries})
        banners = ScoreManager.count_banners_on_tiles(tile_ids, graph)
        return float((2 * len(tile_ids)) + (2 * banners))
    if land_type == "M":
        return 9.0
    return 0.0


def _count_open_edges(
    component_entries: list[tuple[int, list[str]]], graph: Any
) -> int:
    """Count open cardinal edges for a Road or City component.

    The directions stored in the component are tile-relative, so they are
    converted to board-relative directions before checking graph neighbors.

    Args:
        component_entries: Entries describing the component.
        graph: Game graph object.

    Returns:
        Number of open cardinal edges for the component.
    """
    component_tile_ids = {tile_id for tile_id, _ in component_entries}
    open_edges = 0

    for tile_id, directions in component_entries:
        vertex = graph.vertices.get(tile_id)
        if vertex is None:
            continue

        for raw_direction in directions:
            if raw_direction not in CARDINAL_DIRECTIONS:
                continue

            oriented_direction = (
                ScoreManager._convert_tile_direction_to_board_direction(
                    tile_id, raw_direction, graph
                )
            )
            if oriented_direction is None:
                continue

            direction_int = DIRECTION_MAP.get(oriented_direction)
            if direction_int is None:
                continue

            if direction_int not in vertex.neighbors:
                open_edges += 1
                continue

            neighbor_id = vertex.neighbors[direction_int]
            if neighbor_id not in component_tile_ids:
                open_edges += 1

    return open_edges


def _remaining_to_completion(
    land_type: str, component_entries: list[tuple[int, list[str]]], graph: Any
) -> int:
    """Estimate how many open connections remain before completion.

    Current approximation:
    - Monasteries use the number of surrounding occupied tiles.
    - Cities and Roads use the number of still-open cardinal edges.

    Args:
        land_type: Type of component (``"R"``, ``"C"``, ``"M"``).
        component_entries: Entries describing the component.
        graph: Game graph object.

    Returns:
        Number of remaining closures needed to complete the component.
    """
    if land_type == "M":
        if not component_entries:
            return 8
        tile_id, _ = component_entries[0]
        surrounded = ScoreManager._count_surrounding_tiles(tile_id, graph)
        return max(0, 8 - surrounded)

    return _count_open_edges(component_entries, graph)


def _imminence_factor(remaining_to_completion: int) -> float:
    """Map remaining openings to a near-term completion weight.

    Args:
        remaining_to_completion: Estimated remaining closures.

    Returns:
        A weight in ``[0, 1]`` that reflects how likely the component is to
        convert very soon:
        - 1 remaining opening => 1.0
        - 2 remaining openings => 0.45
        - 3 or more => 0.0
    """
    if remaining_to_completion <= 0:
        return 0.0
    if remaining_to_completion == 1:
        return 1.0
    if remaining_to_completion == 2:
        return 0.45
    return 0.0


def _player_component_presence(
    component_name: str, counts: dict[str, dict[int, int]], player_id: int
) -> int:
    """Return the number of meeples a player has on one component.

    Args:
        component_name: Name of the component to inspect.
        counts: Meeple counts per component/per player.
        player_id: Identifier of the player.

    Returns:
        Number of meeples that player has committed to the component.
    """
    return counts.get(component_name, {}).get(player_id, 0)


def _short_term_profile(game_state: Any, player_id: int) -> dict[str, float]:
    """Build the short-term tactical profile for one player.

    The profile keeps only signals meant to matter in the next few turns:
    current score, current meeple stock, near-finished controlled components,
    and likely meeple recoveries.

    Args:
        game_state: Current game state object.
        player_id: Identifier of the player to evaluate.

    Returns:
        Mapping from short-term feature names to their values for that player.
    """
    graph = game_state.game_data.graph
    counts = _component_meeple_counts(game_state)
    imminent_points = 0.0
    imminent_meeple_returns = 0.0
    ready_components = 0.0
    pressure_components = 0.0

    for land_type in ("C", "R", "M"):
        for component_name, entries in graph.lands_components.get(
            land_type, {}
        ).items():
            remaining = _remaining_to_completion(land_type, entries, graph)
            factor = _imminence_factor(remaining)
            if factor <= 0.0:
                continue

            controllers = _component_controllers(component_name, counts)
            if player_id in controllers:
                # Tied control splits the estimated tactical value equally.
                share = 1.0 / len(controllers)
                imminent_points += (
                    share
                    * factor
                    * _estimate_completion_points(land_type, entries, graph)
                )
                if remaining == 1:
                    ready_components += share
                elif remaining == 2:
                    pressure_components += share

            player_meeples = _player_component_presence(
                component_name, counts, player_id
            )
            if player_meeples > 0:
                # Meeple recovery is valued even without sole control because
                # freeing meeples quickly increases short-term flexibility.
                imminent_meeple_returns += factor * float(player_meeples)

    return {
        "score": _get_player_score(game_state, player_id),
        "available_meeples": _get_player_meeples(game_state, player_id),
        "imminent_points": imminent_points,
        "imminent_meeple_returns": imminent_meeple_returns,
        "ready_components": ready_components,
        "pressure_components": pressure_components,
    }


def extract_features(
    game_state: Any, player_id: int, opponent_id: int
) -> dict[str, float]:
    """Extract short-term tactical features as differentials.

    Args:
        game_state: Current game state object.
        player_id: Identifier of the evaluated player.
        opponent_id: Identifier of the compared opponent.

    Returns:
        Differential feature mapping ``player - opponent``.
    """
    player_profile = _short_term_profile(game_state, player_id)
    opponent_profile = _short_term_profile(game_state, opponent_id)

    return {
        "score_diff": player_profile["score"] - opponent_profile["score"],
        "available_meeples_diff": (
            player_profile["available_meeples"]
            - opponent_profile["available_meeples"]
        ),
        "imminent_points_diff": (
            player_profile["imminent_points"]
            - opponent_profile["imminent_points"]
        ),
        "imminent_meeple_returns_diff": (
            player_profile["imminent_meeple_returns"]
            - opponent_profile["imminent_meeple_returns"]
        ),
        "ready_components_diff": (
            player_profile["ready_components"]
            - opponent_profile["ready_components"]
        ),
        "pressure_components_diff": (
            player_profile["pressure_components"]
            - opponent_profile["pressure_components"]
        ),
    }


def _compress_to_star_bounds(
    raw_value: float,
    bias: float = DEFAULT_COMPRESSION_BIAS,
    scale: float = DEFAULT_COMPRESSION_SCALE,
) -> float:
    """Compress a raw heuristic value into ``[-100, 100]`` with a sigmoid.

    Args:
        raw_value: Linear heuristic value before compression.
        bias: Centering value applied before the sigmoid.
        scale: Divisor controlling sensitivity around 0.

    Returns:
        Rounded heuristic value in the STAR-compatible range ``[-100, 100]``.
    """
    if scale <= 0:
        raise ValueError("Compression scale must be > 0.")

    centered_value = (raw_value - bias) / scale
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
    weights: ShortTermWeights = DEFAULT_WEIGHTS,
) -> float:
    """Compute short-term tactical value for one game state.

    Higher values mean the position looks better for ``player_id`` in the
    short term, especially through near-finished structures and upcoming
    meeple recovery.

    Args:
        game_state: Current game state object.
        player_id: Identifier of the evaluated player.
        opponent_id: Identifier of the compared opponent.
        weights: Linear weights applied to the extracted features.

    Returns:
        Compressed heuristic value in ``[-100, 100]``.
    """
    features = extract_features(game_state, player_id, opponent_id)
    raw_value = (
        weights.score_diff * features["score_diff"]
        + weights.available_meeples_diff
        * features["available_meeples_diff"]
        + weights.imminent_points_diff * features["imminent_points_diff"]
        + weights.imminent_meeple_returns_diff
        * features["imminent_meeple_returns_diff"]
        + weights.ready_components_diff * features["ready_components_diff"]
        + weights.pressure_components_diff
        * features["pressure_components_diff"]
    )
    return _compress_to_star_bounds(raw_value)
