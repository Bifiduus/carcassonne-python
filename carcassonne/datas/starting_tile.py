"""Starting-tile initialization helpers.

These functions initialize the starting tile on a provided GraphData
instance. They were extracted from `GraphData` to decouple graph state
from game startup configuration.
"""

from typing import Any


def initialize_starting_tile(graph: Any) -> None:
    """Initialize the default starting tile (CRFR) on the graph."""
    graph.add_vertex(
        vertex_id=0, name="CRFR", middle="", orientation=0, position=(0, 0)
    )
    tile = graph.tiles_dict["CRFR"]
    for land in tile.tiles_lands.keys():
        for connected in tile.tiles_lands[land]:
            land_id = land + str(graph.next_set_id[land])
            graph.lands_components[land][land_id] = [(0, connected)]
            graph.next_set_id[land] += 1


def initialize_starting_tile_river(graph: Any) -> None:
    """Initialize the river starting tile (FFSF) on the graph."""
    graph.add_vertex(
        vertex_id=0, name="FFSF", middle="", orientation=0, position=(0, 0)
    )
    tile = graph.tiles_dict["FFSF"]
    for land in tile.tiles_lands.keys():
        for connected in tile.tiles_lands[land]:
            land_id = land + str(graph.next_set_id[land])
            graph.lands_components[land][land_id] = [(0, connected)]
            graph.next_set_id[land] += 1
