"""This module defines the GraphLogic class, which provides methods for graph-related operations in the Carcassonne game.
The GraphLogic class includes methods for finding the shortest path between two vertices and for identifying connected components in the graph. 
It interacts with the IGraphData interface to access the graph data structure representing the game state.
"""
from typing import List, Optional, Dict, Tuple

from carcassonne.BusinessLogic.Interfaces.IGraphData import IGraphData

from carcassonne.Datas.GraphData import NORTH_DIR, EAST_DIR, SOUTH_DIR, WEST_DIR
from carcassonne.Datas.TilesInfo import TilesInfo

NORTHWEST_MATRIX = (0, 0)
NORTH_MATRIX = (0, 1)
NORTHEAST_MATRIX = (0, 2)
WEST_MATRIX = (1, 0)
CENTER_MATRIX = (1, 1)
EAST_MATRIX = (1, 2)
SOUTHWEST_MATRIX = (2, 0)
SOUTH_MATRIX = (2, 1)
SOUTHEAST_MATRIX = (2, 2)

class GraphLogic:

    corners = ['NW', 'NE', 'SW', 'SE']
    match_corners = {
        'NW': [0, 3],
        'NE': [0, 1],
        'SW': [2, 3],
        'SE': [2, 1]
    }
    
    match_cardinals = {
        'N': 0,
        'E': 1,
        'S': 2,
        'W': 3
    }

    opposite_corners = {
        'NW': ['SW', 'NE'],
        'NE': ['SE', 'NW'],
        'SW': ['NW', 'SE'],
        'SE': ['NE', 'SW']
    }
    
    opposite_cardinal = {
        'N': 'S',
        'E': 'W',
        'S': 'N',
        'W': 'E'
    }
    
    cardinals = ['N', 'E', 'S', 'W']
    
    match_matrix = {
        'NW': NORTHWEST_MATRIX,
        'N': NORTH_MATRIX,
        'NE': NORTHEAST_MATRIX,
        'W': WEST_MATRIX,
        'C': CENTER_MATRIX,
        'E': EAST_MATRIX,
        'SW': SOUTHWEST_MATRIX,
        'S': SOUTH_MATRIX,
        'SE': SOUTHEAST_MATRIX 
    }

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

    def add_lands_components(self, tile_id: int, graph: IGraphData, tiles_info: TilesInfo) -> None:
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
        
        groups_left = {}
        groups_apparition = {}
        for land_type, direction_groups in tile_def.tiles_lands.items():
            for drg in direction_groups:
                groups_left[tuple(drg)] = False
                groups_apparition[tuple(drg)] = 0

        tile_orientation = vertex.orientation
        
        neighbors = vertex.get_neighbors()
        
        for card in self.cardinals:
            next_side_0 = card
            next_side = tile_def.direction_matrix[tile_orientation][self.match_matrix[next_side_0][0]][self.match_matrix[next_side_0][1]]
            next_dir = self.match_cardinals.get(next_side_0)
            if next_dir in neighbors.keys():
                next_neighbor_id = neighbors[next_dir]
                self.handle_cardinal_connection(
                    self, tile_id, next_neighbor_id, next_side_0, next_side, graph, tile_def, tiles_info, groups_left, groups_apparition
                )
                
        for corner in self.corners:
            next_side_0 = corner
            next_side = tile_def.direction_matrix[tile_orientation][self.match_matrix[next_side_0][0]][self.match_matrix[next_side_0][1]]
            next_dir = self.match_cardinals.get(next_side_0)
            if next_dir in neighbors.keys():
                next_neighbor_id = neighbors[next_dir]
                special_corner = tile_def.connect_to.get(next_side)
                # Special corner is for example : NW Field with Field connection to the West and City connection to the North.
                # So we can't just take the land type of the corner.
                if special_corner is not None:
                    self.handle_special_corner_connection(
                        self,tile_id, tile_orientation, next_neighbor_id, next_side_0, next_side, graph, tile_def, tiles_info, special_corner, 0, groups_left, groups_apparition
                    )
                else :
                    self.handle_corner_connection(
                        self, tile_id, next_neighbor_id, next_side_0, next_side, graph, tile_def, tiles_info, 0, groups_left, groups_apparition
                    )

            next_dir = self.match_cardinals.get(next_side_0)
            if next_dir in neighbors.keys():
                next_neighbor_id = neighbors[next_dir]
                special_corner = tile_def.connect_to.get(next_side)
                # Special corner is for example : NW Field with Field connection to the West and City connection to the North.
                # So we can't just take the land type of the corner.
                if special_corner is not None:
                    self.handle_special_corner_connection(
                        self, tile_id, tile_orientation, next_neighbor_id, next_side_0, next_side, graph, tile_def, tiles_info, special_corner, 1, groups_left, groups_apparition
                    )
                else :
                    self.handle_corner_connection(
                        self, tile_id, next_neighbor_id, next_side_0, next_side, graph, tile_def, tiles_info, 1, groups_left, groups_apparition
                    )
        
        # Every grp that isn't at True means that it was added to no already existing set, so we need new ones for them
        for grp, bool in groups_left.items():
            if bool == False:
                # Create new land set
                for land_type, direction_groups in tile_def.tiles_lands.items():
                    for drg in direction_groups:
                        if tuple(drg) == grp:
                            land = land_type
                            break
                set_name = self._get_next_set_name(land, graph)
                graph.lands_components[land][set_name] = [
                    (tile_id, grp)
                ]
                groups_left[grp] = True
            
        # Merge the sets that are connected thanks to the tile we just placed 
        for grp, apparition in groups_apparition.items():
            if apparition > 1:
                # We need to merge the sets that have the same grp
                sets_to_merge = []
                for land_type, sets in graph.lands_components.items():
                    for set_name, set_list in sets.items():
                        for _, drg in set_list:
                            if drg == grp:
                                sets_to_merge.append((land_type, set_name))
                                break
                # Merge all sets in sets_to_merge into the first one
                main_set = sets_to_merge[0]
                for other_set in sets_to_merge[1:]:
                    graph.lands_components[main_set[0]][main_set[1]].extend(graph.lands_components[other_set[0]][other_set[1]])
                    for set_name in list(graph.lands_components[other_set[0]].keys()):
                        for meeple in graph.get_meeples():
                            if meeple.lands_components == other_set[1]:
                                meeple.lands_components = main_set[1]
                    del graph.lands_components[other_set[0]][other_set[1]]

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
    def handle_special_corner_connection(self, tile_id: int, tile_orientation: int, neighbor_id: int, initial_corner: str, corner: str, graph: IGraphData, tile_def, tiles_info, special_corner, corner_number, groups_left, groups_apparition) -> None:
        # Find the special land type in the corner
        land = None
        corner_grp = None
        for land_type, direction_groups in tile_def.tiles_lands.items():
            for drg in direction_groups:
                if corner in drg:
                    land = land_type
                    corner_grp = drg

        if corner_number == 0:
            special_land = special_corner[0] if tile_orientation % 2 == 0 else special_corner[1]
            if special_land != land:
                return
            neigh_initial_corner = self.opposite_corners.get(initial_corner)[0]

        elif corner_number == 1:
            special_land = special_corner[1] if tile_orientation % 2 == 0 else special_corner[0]
            if special_land != land:
                return
            neigh_initial_corner = self.opposite_corners.get(initial_corner)[1]

        neighbor_vertex = graph.get_vertex(neighbor_id)
        neighbor_def = tiles_info.tiles.get(neighbor_vertex.name.split('/')[0])
        
        # Get the opposite corner on neighbor tile
        neigh_orientation = neighbor_vertex.get_orientation()
        nx,ny = self.match_matrix.get(neigh_initial_corner)
        neigh_corner = neighbor_def.direction_matrix[neigh_orientation][nx][ny]

        # Find if neighbor has a direction group containing the opposite position
        neighbor_dir_group = None
        for ndg in neighbor_def.tiles_lands[special_land]:
            if neigh_corner in ndg:
                neighbor_dir_group = ndg
                break

        if neighbor_dir_group == None:
            return
        # Means we have the same land for the two tiles
        else:
            existing_set = self._find_lands_set(special_land, neighbor_id, neighbor_dir_group, graph)
            existing_set.append((tile_id, corner_grp))
            groups_left[tuple(corner_grp)] = True
            groups_apparition[tuple(corner_grp)] += 1

    @staticmethod
    def handle_corner_connection(self, tile_id: int, neighbor_id: int, initial_corner: str, corner: str, graph: IGraphData, tile_def, tiles_info, corner_number, groups_left, groups_apparition):
        # Find the land type in the corner
        land = None
        corner_grp = None
        for land_type, direction_groups in tile_def.tiles_lands.items():
            for drg in direction_groups:
                if corner in drg:
                    land = land_type
                    corner_grp = drg

        if corner_number == 0:
            neigh_initial_corner = self.opposite_corners.get(initial_corner)[0]

        elif corner_number == 1:
            neigh_initial_corner = self.opposite_corners.get(initial_corner)[1]

        neighbor_vertex = graph.get_vertex(neighbor_id)
        neighbor_def = tiles_info.tiles.get(neighbor_vertex.name.split('/')[0])
        
        # Get the opposite corner on neighbor tile
        neigh_orientation = neighbor_vertex.get_orientation()
        nx,ny = self.match_matrix.get(neigh_initial_corner)
        neigh_corner = neighbor_def.direction_matrix[neigh_orientation][nx][ny]

        # Find if neighbor has a direction group containing the opposite position
        neighbor_dir_group = None
        for ndg in neighbor_def.tiles_lands[land]:
            if neigh_corner in ndg:
                neighbor_dir_group = ndg
                break
        
        if neighbor_dir_group == None:
            return
        # Means we have the same land for the two tiles
        else:
            existing_set = self._find_lands_set(land, neighbor_id, neighbor_dir_group, graph)
            existing_set.append((tile_id, corner_grp))
            groups_left[tuple(corner_grp)] = True
            groups_apparition[tuple(corner_grp)] += 1

    @staticmethod
    def handle_cardinal_connection(self, tile_id: int, neighbor_id: int, initial_corner: str, cardinal: str, graph: IGraphData, tile_def, tiles_info, groups_left, groups_apparition):
        # Find the land type of the cardinal
        land = None
        card_grp = None
        for land_type, direction_groups in tile_def.tiles_lands.items():
            for drg in direction_groups:
                if cardinal in drg:
                    land = land_type
                    card_grp = drg

        neigh_initial_corner = self.opposite_cardinal.get(initial_corner)

        neighbor_vertex = graph.get_vertex(neighbor_id)
        neighbor_def = tiles_info.tiles.get(neighbor_vertex.name.split('/')[0])
        
        # Get the opposite corner on neighbor tile
        neigh_orientation = neighbor_vertex.get_orientation()
        nx,ny = self.match_matrix.get(neigh_initial_corner)
        neigh_corner = neighbor_def.direction_matrix[neigh_orientation][nx][ny]

        # Find if neighbor has a direction group containing the opposite position
        neighbor_dir_group = None
        for ndg in neighbor_def.tiles_lands[land]:
            if neigh_corner in ndg:
                neighbor_dir_group = ndg
                break
        
        if neighbor_dir_group == None:
            return
        # Means we have the same land for the two tiles
        else:
            existing_set = self._find_lands_set(land, neighbor_id, neighbor_dir_group, graph)
            existing_set.append((tile_id, card_grp))
            groups_left[tuple(card_grp)] = True
            groups_apparition[tuple(card_grp)] += 1
