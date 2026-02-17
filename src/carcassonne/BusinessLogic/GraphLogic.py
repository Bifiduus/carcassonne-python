"""This module defines the GraphLogic class, which provides methods for graph-related operations in the Carcassonne game.
The GraphLogic class includes methods for finding the shortest path between two vertices and for identifying connected components in the graph. 
It interacts with the IGraphData interface to access the graph data structure representing the game state.
"""
from typing import List, Optional, Dict, Tuple

from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData

from carcassonne.Datas.GraphData import NORTH_DIR, EAST_DIR, SOUTH_DIR, WEST_DIR
from carcassonne.Datas.TilesInfo import TilesInfo

class GraphLogic:
    @staticmethod
    def add_lands_components(tile_id: int, graph: IGraphData, tiles_info: TilesInfo) -> None:
        """Add lands components for a newly placed tile, connecting to neighbors where applicable.

        Args:
            tile_id: The ID of the newly placed tile
            graph: The game graph
            tiles_info: Tile definitions with land data
        """
        if tile_id not in graph.vertices:
            return

        vertex = graph.vertices[tile_id]
        tile_def = tiles_info.tiles.get(vertex.name.split('/')[0])
        if tile_def is None or not tile_def.tiles_lands:
            return

        tile_orientation = vertex.orientation

        # Direction constants and mappings
        opposite_dir = {NORTH_DIR: SOUTH_DIR, EAST_DIR: WEST_DIR, SOUTH_DIR: NORTH_DIR, WEST_DIR: EAST_DIR}
        direction_matrix_indices = {
            NORTH_DIR: (0, 1),
            EAST_DIR: (1, 2),
            SOUTH_DIR: (2, 1),
            WEST_DIR: (1, 0)
        }
        # Diagonal positions for cardinal directions (for R/S special handling)
        diagonal_positions = {
            NORTH_DIR: (0, 0, 0, 2),   # NW and NE
            EAST_DIR: (0, 2, 2, 2),    # NE and SE
            SOUTH_DIR: (2, 2, 2, 0),   # SE and SW
            WEST_DIR: (2, 0, 0, 0)     # SW and NW
        }

        # Process each land type in the tile
        for land_type, direction_groups in tile_def.tiles_lands.items():
            if land_type == 'M':  # Monastery
                set_name = GraphLogic._get_next_set_name(land_type, graph)
                graph.lands_components[land_type][set_name] = [(tile_id, None)]
                continue

            # For other lands (F, C, R, S)
            for direction_group in direction_groups:
                # Check each cardinal direction
                for direction in [NORTH_DIR, EAST_DIR, SOUTH_DIR, WEST_DIR]:
                    if direction not in vertex.neighbors:
                        continue

                    neighbor_id = vertex.neighbors[direction]
                    if neighbor_id not in graph.vertices:
                        continue

                    neighbor_vertex = graph.vertices[neighbor_id]
                    neighbor_def = tiles_info.tiles.get(neighbor_vertex.name.split('/')[0])
                    if neighbor_def is None:
                        continue

                    neighbor_orientation = neighbor_vertex.orientation

                    # Get position labels for cardinal direction
                    row, col = direction_matrix_indices[direction]
                    pos = tile_def.direction_matrix[tile_orientation][row][col]

                    # Check if this direction group contains the cardinal position
                    if pos not in direction_group:
                        continue

                    # Check if neighbor has same land at opposite direction
                    opp_dir = opposite_dir[direction]
                    opp_row, opp_col = direction_matrix_indices[opp_dir]
                    opp_pos = neighbor_def.direction_matrix[neighbor_orientation][opp_row][opp_col]

                    # Check if neighbor has this land type
                    if land_type not in neighbor_def.tiles_lands:
                        continue

                    # Find if neighbor has a direction group containing the opposite position
                    neighbor_dir_group = None
                    for ndg in neighbor_def.tiles_lands[land_type]:
                        if opp_pos in ndg:
                            neighbor_dir_group = ndg
                            break

                    if neighbor_dir_group is None:
                        continue

                    # lands match at cardinal direction
                    # Try to find existing land set containing neighbor
                    existing_set = GraphLogic._find_lands_set(
                        land_type, neighbor_id, neighbor_dir_group, graph
                    )

                    if existing_set:
                        # Add tile to existing set
                        existing_set.append((tile_id, direction_group))
                    else:
                        # Create new land set
                        set_name = GraphLogic._get_next_set_name(land_type, graph)
                        graph.lands_components[land_type][set_name] = [
                            (tile_id, direction_group),
                            (neighbor_id, neighbor_dir_group)
                        ]

                    # Special handling for Road (R) and Stream (S) diagonal connections
                    if land_type in ['R', 'S']:
                        GraphLogic._add_diagonal_connections(
                            tile_id, neighbor_id, direction, tile_def, neighbor_def,
                            tile_orientation, neighbor_orientation, graph, diagonal_positions
                        )

    @staticmethod
    def _get_next_set_name(land_type: str, graph: IGraphData) -> str:
        """Get the next set name for a land type (e.g., 'C1', 'F2')."""
        if land_type not in graph.lands_components:
            graph.lands_components[land_type] = {}
            graph.next_set_id[land_type] = 1

        set_id = graph.next_set_id.get(land_type, 1)
        graph.next_set_id[land_type] = set_id + 1
        return f'{land_type}{set_id}'

    @staticmethod
    def _find_lands_set(
        land_type: str, tile_id: int, direction_group: List[str], graph: IGraphData) -> Optional[List[Tuple[int, List[str]]]]:
        """Find a land set that contains the given tile with the given direction group."""
        if land_type not in graph.lands_components:
            return None

        for set_list in graph.lands_components[land_type].values():
            for tid, dg in set_list:
                if tid == tile_id and dg == direction_group:
                    return set_list
        return None

    @staticmethod
    def _add_diagonal_connections(
        tile_id: int, neighbor_id: int, direction: int, tile_def, neighbor_def,
        tile_orientation: int, neighbor_orientation: int, graph: IGraphData, diagonal_positions: Dict
    ) -> None:
        """Handle diagonal land connections for R and S lands."""
        # Get diagonal positions for this cardinal direction
        dir_row1, dir_col1, dir_row2, dir_col2 = diagonal_positions[direction]

        # Get position labels for diagonals
        diag1_pos = tile_def.direction_matrix[tile_orientation][dir_row1][dir_col1]
        diag2_pos = tile_def.direction_matrix[tile_orientation][dir_row2][dir_col2]
        opp_diag1_pos = neighbor_def.direction_matrix[neighbor_orientation][dir_row1][dir_col1]
        opp_diag2_pos = neighbor_def.direction_matrix[neighbor_orientation][dir_row2][dir_col2]

        # For each diagonal, check if Field lands connect
        for diag_pos, opp_diag_pos in [(diag1_pos, opp_diag1_pos), (diag2_pos, opp_diag2_pos)]:
            # Find Field direction groups containing these diagonal positions
            if 'F' not in tile_def.tiles_lands:
                continue

            field_group = None
            for fg in tile_def.tiles_lands['F']:
                if diag_pos in fg:
                    field_group = fg
                    break

            if 'F' not in neighbor_def.tiles_lands:
                continue

            opp_field_group = None
            for fg in neighbor_def.tiles_lands['F']:
                if opp_diag_pos in fg:
                    opp_field_group = fg
                    break

            if field_group and opp_field_group:
                # Both have Field at diagonal -> create or merge connection
                existing_set = GraphLogic._find_lands_set('F', neighbor_id, opp_field_group, graph)
                if existing_set:
                    existing_set.append((tile_id, field_group))
                else:
                    set_name = GraphLogic._get_next_set_name('F', graph)
                    graph.lands_components['F'][set_name] = [
                        (tile_id, field_group),
                        (neighbor_id, opp_field_group)
                    ]

    def add_tile_to_graph(self, move, graph: IGraphData):
        #TODO : add_tile_to_graph(move : str, graph : GraphData) -> None
        pass
