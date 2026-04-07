"""Graph-related operations for the Carcassonne game.

The GraphLogic class finds tile connections and connected components while
interacting with `IGraphData`.
"""

from typing import Dict, List, Optional, Tuple

from carcassonne.business_logic.interfaces.i_graph_data import IGraphData
from carcassonne.datas.tiles_constants import CARDINALS
from carcassonne.datas.tiles_constants import DIRECTION_MAP
from carcassonne.datas.tiles_constants import MATCH_MATRIX
from carcassonne.datas.tiles_constants import OPPOSITE_CARDINAL

from carcassonne.datas.tiles_info import Tile, TilesInfo

DirectionGroup = List[str]
GroupKey = Tuple[str, ...]
ComponentEntry = Tuple[int, DirectionGroup]
ComponentSet = List[ComponentEntry]
LandsSetIndex = Dict[Tuple[str, int, GroupKey], List[ComponentSet]]
GroupIsLinkedMap = Dict[GroupKey, bool]
GroupConnectionCountMap = Dict[GroupKey, int]
GroupLandTypeMap = Dict[GroupKey, str]


class GraphLogic:

    cardinals = list(CARDINALS)

    opposite_cardinal = OPPOSITE_CARDINAL

    match_cardinals = DIRECTION_MAP

    match_matrix = MATCH_MATRIX

    corners = ["NW", "NE", "SW", "SE"]

    match_corners = {"NW": [0, 3], "NE": [0, 1], "SW": [2, 3], "SE": [2, 1]}

    opposite_corners = {
        "NW": ["SW", "NE"],
        "NE": ["SE", "NW"],
        "SW": ["NW", "SE"],
        "SE": ["NE", "SW"],
    }

    def add_lands_components(
        self, tile_id: int, graph: IGraphData, tiles_info: TilesInfo
    ) -> None:
        """Update terrain components after placing one tile.

        The method links tile sides/corners to matching neighbor components,
        creates missing components for unlinked terrain groups, then merges
        groups that became connected through this tile placement.

        Args:
            tile_id: Identifier of the newly placed tile.
            graph: Mutable graph state storing vertices and terrain
                components.
            tiles_info: Tile definitions used to interpret direction groups.

        Returns:
            None. Mutates graph terrain components and related meeple
            component references.
        """

        if tile_id not in graph.vertices:
            return

        vertex = graph.vertices[tile_id]
        tile_def = tiles_info.tiles.get(vertex.name.split("/")[0])
        if tile_def is None or not tile_def.tiles_lands:
            return

        (
            group_is_linked,
            group_connection_count,
            group_land_type,
        ) = self._initialize_group_tracking(tile_def)

        tile_orientation = vertex.orientation
        lands_set_index = self._build_lands_set_index(graph)

        neighbors = vertex.get_neighbors()
        # Connect cardinal sides to neighbor components
        self._process_cardinal_neighbors(
            tile_id,
            tile_orientation,
            neighbors,
            graph,
            tile_def,
            tiles_info,
            group_is_linked,
            group_connection_count,
            lands_set_index,
        )
        # Connect corner groups to neighbor components
        self._process_corner_neighbors(
            tile_id,
            tile_orientation,
            neighbors,
            graph,
            tile_def,
            tiles_info,
            group_is_linked,
            group_connection_count,
            lands_set_index,
        )
        # Create components for unlinked groups
        self._create_unlinked_groups(
            tile_id,
            graph,
            group_is_linked,
            group_land_type,
            lands_set_index,
        )
        # Merge groups that connected multiple times
        self._merge_connected_groups(
            tile_id,
            graph,
            group_connection_count,
            group_land_type,
            lands_set_index,
        )

    def _initialize_group_tracking(
        self,
        tile_def: Tile,
    ) -> Tuple[GroupIsLinkedMap, GroupConnectionCountMap, GroupLandTypeMap]:
        """Build tracking maps for all direction groups on the tile."""
        group_is_linked: GroupIsLinkedMap = {}
        group_connection_count: GroupConnectionCountMap = {}
        group_land_type: GroupLandTypeMap = {}

        for land_type, direction_groups in tile_def.tiles_lands.items():
            for direction_group in direction_groups:
                group_key = tuple(direction_group)
                group_is_linked[group_key] = False
                group_connection_count[group_key] = 0
                group_land_type[group_key] = land_type

        return group_is_linked, group_connection_count, group_land_type

    def _process_cardinal_neighbors(
        self,
        tile_id: int,
        tile_orientation: int,
        neighbors: Dict[int, int],
        graph: IGraphData,
        tile_def: Tile,
        tiles_info: TilesInfo,
        group_is_linked: GroupIsLinkedMap,
        group_connection_count: GroupConnectionCountMap,
        lands_set_index: LandsSetIndex,
    ) -> None:
        """Connect cardinal sides of the tile to neighbor components."""
        for side in self.cardinals:
            # Extract terrain label from the 3x3 tile matrix
            # at the cardinal position.
            # match_matrix maps side labels ("N", "E", "S", "W") to (row, col).
            oriented_side = tile_def.direction_matrix[tile_orientation][
                self.match_matrix[side][0]
            ][self.match_matrix[side][1]]
            neighbor_direction = self.match_cardinals.get(side)
            if neighbor_direction not in neighbors:
                continue

            neighbor_id = neighbors[neighbor_direction]
            self.handle_cardinal_connection(
                tile_id,
                neighbor_id,
                side,
                oriented_side,
                graph,
                tile_def,
                tiles_info,
                group_is_linked,
                group_connection_count,
                lands_set_index,
            )

    def _process_corner_neighbors(
        self,
        tile_id: int,
        tile_orientation: int,
        neighbors: Dict[int, int],
        graph: IGraphData,
        tile_def: Tile,
        tiles_info: TilesInfo,
        group_is_linked: GroupIsLinkedMap,
        group_connection_count: GroupConnectionCountMap,
        lands_set_index: LandsSetIndex,
    ) -> None:
        """Connect corner groups of the current tile to neighbor components."""
        for corner in self.corners:
            # Extract terrain label from the 3x3 tile matrix
            # at the corner position.
            # match_matrix maps corner labels ("NW", "NE", etc.) to (row, col).
            oriented_corner = tile_def.direction_matrix[tile_orientation][
                self.match_matrix[corner][0]
            ][self.match_matrix[corner][1]]
            special_corner = tile_def.connect_to.get(oriented_corner)

            for corner_number, neighbor_direction in enumerate(
                self.match_corners.get(corner, [])
            ):
                if neighbor_direction not in neighbors:
                    continue

                neighbor_id = neighbors[neighbor_direction]
                if special_corner is not None:
                    self.handle_special_corner_connection(
                        tile_id,
                        tile_orientation,
                        neighbor_id,
                        corner,
                        oriented_corner,
                        graph,
                        tile_def,
                        tiles_info,
                        special_corner,
                        corner_number,
                        group_is_linked,
                        group_connection_count,
                        lands_set_index,
                    )
                else:
                    self.handle_corner_connection(
                        tile_id,
                        neighbor_id,
                        corner,
                        oriented_corner,
                        graph,
                        tile_def,
                        tiles_info,
                        corner_number,
                        group_is_linked,
                        group_connection_count,
                        lands_set_index,
                    )

    def _create_unlinked_groups(
        self,
        tile_id: int,
        graph: IGraphData,
        group_is_linked: GroupIsLinkedMap,
        group_land_type: GroupLandTypeMap,
        lands_set_index: LandsSetIndex,
    ) -> None:
        """Create components for groups that did not connect to neighbors."""
        for group_key, is_linked in group_is_linked.items():
            if is_linked:
                continue

            land_type = group_land_type.get(group_key)
            if land_type is None:
                continue

            set_name = self._get_next_set_name(land_type, graph)
            graph.lands_components[land_type][set_name] = [
                (tile_id, list(group_key))
            ]
            self._index_set_entry(
                lands_set_index,
                land_type,
                tile_id,
                list(group_key),
                graph.lands_components[land_type][set_name],
            )
            group_is_linked[group_key] = True

    def _merge_connected_groups(
        self,
        tile_id: int,
        graph: IGraphData,
        group_connection_count: GroupConnectionCountMap,
        group_land_type: GroupLandTypeMap,
        lands_set_index: LandsSetIndex,
    ) -> None:
        """Merge components linked multiple times through one placed tile."""
        for group_key, connection_count in group_connection_count.items():
            if connection_count <= 1:
                continue

            land_type = group_land_type.get(group_key)
            if land_type is None:
                continue
            sets_to_merge = self._collect_sets_to_merge(
                land_type,
                tile_id,
                group_key,
                graph,
                lands_set_index,
            )
            if len(sets_to_merge) < 2:
                continue
            self._merge_set_names(
                land_type,
                sets_to_merge,
                graph,
                lands_set_index,
            )

    def _collect_sets_to_merge(
        self,
        land_type: str,
        tile_id: int,
        group_key: GroupKey,
        graph: IGraphData,
        lands_set_index: LandsSetIndex,
    ) -> List[str]:
        """Collect component names that must be merged for one group key."""
        # Use object id() to map list references back to component names,
        # since the index stores list objects but we need their string keys.
        set_names_by_list_id = {
            id(set_list): set_name
            for set_name, set_list in graph.lands_components.get(
                land_type, {}
            ).items()
        }
        linked_sets = lands_set_index.get((land_type, tile_id, group_key), [])
        sets_to_merge: List[str] = []
        for set_list in linked_sets:
            set_name = set_names_by_list_id.get(id(set_list))
            if set_name is not None and set_name not in sets_to_merge:
                sets_to_merge.append(set_name)
        return sets_to_merge

    def _merge_set_names(
        self,
        land_type: str,
        sets_to_merge: List[str],
        graph: IGraphData,
        lands_set_index: LandsSetIndex,
    ) -> None:
        """Merge all component names into the first component name."""
        main_set_name = sets_to_merge[0]
        for other_set_name in sets_to_merge[1:]:
            other_set_entries = graph.lands_components[land_type][
                other_set_name
            ]
            graph.lands_components[land_type][main_set_name].extend(
                other_set_entries
            )
            main_set_entries = graph.lands_components[land_type][main_set_name]
            for tid, direction_group in other_set_entries:
                self._replace_index_set_reference(
                    lands_set_index,
                    land_type,
                    tid,
                    direction_group,
                    graph.lands_components[land_type][other_set_name],
                    main_set_entries,
                )
            # Redirect all meeples from the old component to the merged one
            # to maintain ownership consistency after merge.
            for meeple in getattr(graph, "meeples", []):
                if meeple.lands_components == other_set_name:
                    meeple.lands_components = main_set_name
            del graph.lands_components[land_type][other_set_name]

    @staticmethod
    def _get_next_set_name(land_type: str, graph: IGraphData) -> str:
        """Generate the next component identifier for one terrain type.

        Args:
            land_type: Terrain key such as `C`, `R`, `F`, `M`, or `S`.
            graph: Graph state containing component registries and counters.

        Returns:
            A unique component name for the given terrain type.
        """
        if land_type not in graph.lands_components:
            graph.lands_components[land_type] = {}
            graph.next_set_id[land_type] = 1

        set_id = graph.next_set_id.get(land_type, 1)
        graph.next_set_id[land_type] = set_id + 1
        return f"{land_type}{set_id}"

    @staticmethod
    def _find_component_set(
        land_type: str,
        tile_id: int,
        direction_group: DirectionGroup,
        graph: IGraphData,
        lands_set_index: Optional[LandsSetIndex] = None,
    ) -> Optional[ComponentSet]:
        """Find the component list containing a tile direction group.

        When a local index is provided, lookup is performed through that index
        first; otherwise a linear scan over graph components is used.

        Args:
            land_type: Terrain key to search inside.
            tile_id: Tile identifier to match.
            direction_group: Direction-group labels to match on the tile.
            graph: Graph state containing terrain components.
            lands_set_index: Optional local acceleration index built for one
                add operation.

        Returns:
            The component list containing the entry, or None if not found.
        """
        if lands_set_index is not None:
            key = (land_type, tile_id, tuple(direction_group))
            matching_sets = lands_set_index.get(key, [])
            if matching_sets:
                return matching_sets[0]

        if land_type not in graph.lands_components:
            return None

        for set_list in graph.lands_components[land_type].values():
            for tid, dg in set_list:
                if tid == tile_id and dg == direction_group:
                    return set_list
        return None

    @staticmethod
    def _build_lands_set_index(
        graph: IGraphData,
    ) -> LandsSetIndex:
        """Build a temporary component lookup index for one update pass.

        Args:
            graph: Graph state containing current terrain components.

        Returns:
            A dictionary mapping (land_type, tile_id, direction_group_tuple)
            to one or more component lists containing that entry.
        """
        lands_set_index: LandsSetIndex = {}
        for land_type, components in graph.lands_components.items():
            for set_list in components.values():
                for tid, drg in set_list:
                    GraphLogic._index_set_entry(
                        lands_set_index,
                        land_type,
                        tid,
                        drg,
                        set_list,
                    )
        return lands_set_index

    @staticmethod
    def _index_set_entry(
        lands_set_index: LandsSetIndex,
        land_type: str,
        tile_id: int,
        direction_group: DirectionGroup,
        set_list: ComponentSet,
    ) -> None:
        """Associate one tile/group key with the component list containing it.

        Args:
            lands_set_index: Mutable local lookup index.
            land_type: Terrain key of the component.
            tile_id: Tile identifier stored in the component.
            direction_group: Direction-group labels for this tile entry.
            set_list: Component list object that owns the entry.

        Returns:
            None. Mutates the index in place.
        """
        key = (land_type, tile_id, tuple(direction_group))
        linked_sets = lands_set_index.setdefault(key, [])
        if set_list not in linked_sets:
            linked_sets.append(set_list)

    @staticmethod
    def _replace_index_set_reference(
        lands_set_index: LandsSetIndex,
        land_type: str,
        tile_id: int,
        direction_group: DirectionGroup,
        old_set: ComponentSet,
        new_set: ComponentSet,
    ) -> None:
        """Replace a component-list reference inside the local index.

        Used during merges so keys previously pointing to old_set point to
        new_set instead.

        Args:
            lands_set_index: Mutable local lookup index.
            land_type: Terrain key of the entry.
            tile_id: Tile identifier of the entry.
            direction_group: Direction-group labels of the entry.
            old_set: Previous component list reference.
            new_set: Replacement component list reference.

        Returns:
            None. Mutates the index in place.
        """
        key = (land_type, tile_id, tuple(direction_group))
        linked_sets = lands_set_index.get(key)
        if not linked_sets:
            return
        replaced_sets = [new_set if s is old_set else s for s in linked_sets]
        deduplicated_sets = []
        for set_ref in replaced_sets:
            if set_ref not in deduplicated_sets:
                deduplicated_sets.append(set_ref)
        lands_set_index[key] = deduplicated_sets

    @staticmethod
    def _find_land_and_group_for_side(
        tile_def: Tile,
        side: str,
    ) -> Tuple[Optional[str], Optional[DirectionGroup]]:
        """Resolve the terrain type and group owning one side label.

        Args:
            tile_def: Tile definition containing tiles_lands mapping.
            side: Side label to resolve (`N`, `E`, `S`, `W`, or corner label).

        Returns:
            Tuple (land_type, direction_group) if found, otherwise
            (None, None).
        """
        for land_type, direction_groups in tile_def.tiles_lands.items():
            for direction_group in direction_groups:
                if side in direction_group:
                    return land_type, direction_group
        return None, None

    @staticmethod
    def _find_neighbor_group(
        neighbor_def: Tile,
        land_type: str,
        neighbor_side: str,
    ) -> Optional[DirectionGroup]:
        """Find the neighbor direction group containing a target side label.

        Args:
            neighbor_def: Neighbor tile definition containing tiles_lands.
            land_type: Terrain key to inspect on the neighbor.
            neighbor_side: Side label that must belong to the returned group.

        Returns:
            The matching neighbor direction group, or None if absent.
        """
        neighbor_direction_groups = neighbor_def.tiles_lands.get(land_type)
        if neighbor_direction_groups is None:
            return None

        for direction_group in neighbor_direction_groups:
            if neighbor_side in direction_group:
                return direction_group
        return None

    def handle_special_corner_connection(
        self,
        tile_id: int,
        tile_orientation: int,
        neighbor_id: int,
        initial_corner: str,
        corner: str,
        graph: IGraphData,
        tile_def: Tile,
        tiles_info: TilesInfo,
        special_corner: List[str],
        corner_number: int,
        group_is_linked: GroupIsLinkedMap,
        group_connection_count: GroupConnectionCountMap,
        lands_set_index: LandsSetIndex,
    ) -> None:
        """Handle corner connection when connect_to defines split terrain.

        Some corners can connect to different land types depending on
        orientation and neighbor side. This method applies that special rule,
        then links the current tile group to the matched neighbor component.

        Args:
            tile_id: Current tile identifier.
            tile_orientation: Current tile orientation index.
            neighbor_id: Adjacent tile identifier.
            initial_corner: Corner label on current tile before orientation
                mapping.
            corner: Effective oriented corner label on current tile.
            graph: Mutable graph state.
            tile_def: Current tile definition.
            tiles_info: All tile definitions.
            special_corner: connect_to mapping payload for this corner.
            corner_number: Neighbor relation selector (0 or 1) for the corner.
            group_is_linked: Map tracking whether each current group was
                linked.
            group_connection_count: Map counting how many links each group
                formed.
            lands_set_index: Local component lookup index for this add pass.

        Returns:
            None. Mutates component lists and tracking maps when a connection
            exists.
        """
        land, corner_grp = self._find_land_and_group_for_side(tile_def, corner)
        if land is None or corner_grp is None:
            return

        if corner_number == 0:
            # Even/odd orientation determines which terrain of the split
            # corner connects to this neighbor side.
            special_land = (
                special_corner[0]
                if tile_orientation % 2 == 0
                else special_corner[1]
            )
            if special_land != land:
                return
            neigh_initial_corner = self.opposite_corners.get(initial_corner)[0]

        elif corner_number == 1:
            special_land = (
                special_corner[1]
                if tile_orientation % 2 == 0
                else special_corner[0]
            )
            if special_land != land:
                return
            neigh_initial_corner = self.opposite_corners.get(initial_corner)[1]
        else:
            return

        neighbor_vertex = graph.get_vertex(neighbor_id)
        neighbor_def = tiles_info.tiles.get(neighbor_vertex.name.split("/")[0])
        neigh_orientation = neighbor_vertex.get_orientation()
        nx, ny = self.match_matrix.get(neigh_initial_corner)
        neigh_corner = neighbor_def.direction_matrix[neigh_orientation][nx][ny]

        # Check if neighbor has matching terrain at the opposite position
        neighbor_dir_group = self._find_neighbor_group(
            neighbor_def, special_land, neigh_corner
        )

        if neighbor_dir_group is None:
            return

        # Link current group to existing neighbor component
        existing_set = self._find_component_set(
            special_land,
            neighbor_id,
            neighbor_dir_group,
            graph,
            lands_set_index,
        )
        if existing_set is None:
            return
        existing_set.append((tile_id, corner_grp))
        self._index_set_entry(
            lands_set_index,
            special_land,
            tile_id,
            corner_grp,
            existing_set,
        )
        group_is_linked[tuple(corner_grp)] = True
        group_connection_count[tuple(corner_grp)] += 1

    def handle_corner_connection(
        self,
        tile_id: int,
        neighbor_id: int,
        initial_corner: str,
        corner: str,
        graph: IGraphData,
        tile_def: Tile,
        tiles_info: TilesInfo,
        corner_number: int,
        group_is_linked: GroupIsLinkedMap,
        group_connection_count: GroupConnectionCountMap,
        lands_set_index: LandsSetIndex,
    ) -> None:
        """Handle a standard corner-to-corner terrain connection.

        Args:
            tile_id: Current tile identifier.
            neighbor_id: Adjacent tile identifier.
            initial_corner: Corner label on current tile before orientation
                mapping.
            corner: Effective oriented corner label on current tile.
            graph: Mutable graph state.
            tile_def: Current tile definition.
            tiles_info: All tile definitions.
            corner_number: Neighbor relation selector (0 or 1) for the corner.
            group_is_linked: Map tracking whether each current group was
                linked.
            group_connection_count: Map counting how many links each group
                formed.
            lands_set_index: Local component lookup index for this add pass.

        Returns:
            None. Mutates component lists and tracking maps when a connection
            exists.
        """
        land, corner_grp = self._find_land_and_group_for_side(tile_def, corner)
        if land is None or corner_grp is None:
            return

        if corner_number == 0:
            neigh_initial_corner = self.opposite_corners.get(initial_corner)[0]

        elif corner_number == 1:
            neigh_initial_corner = self.opposite_corners.get(initial_corner)[1]
        else:
            return

        neighbor_vertex = graph.get_vertex(neighbor_id)
        neighbor_def = tiles_info.tiles.get(neighbor_vertex.name.split("/")[0])
        neigh_orientation = neighbor_vertex.get_orientation()
        nx, ny = self.match_matrix.get(neigh_initial_corner)
        neigh_corner = neighbor_def.direction_matrix[neigh_orientation][nx][ny]

        # Check if neighbor has matching terrain at the opposite corner
        neighbor_dir_group = self._find_neighbor_group(
            neighbor_def, land, neigh_corner
        )

        if neighbor_dir_group is None:
            return

        # Link current group to existing neighbor component
        existing_set = self._find_component_set(
            land,
            neighbor_id,
            neighbor_dir_group,
            graph,
            lands_set_index,
        )
        if existing_set is None:
            return
        existing_set.append((tile_id, corner_grp))
        self._index_set_entry(
            lands_set_index,
            land,
            tile_id,
            corner_grp,
            existing_set,
        )
        group_is_linked[tuple(corner_grp)] = True
        group_connection_count[tuple(corner_grp)] += 1

    def handle_cardinal_connection(
        self,
        tile_id: int,
        neighbor_id: int,
        initial_side: str,
        cardinal: str,
        graph: IGraphData,
        tile_def: Tile,
        tiles_info: TilesInfo,
        group_is_linked: GroupIsLinkedMap,
        group_connection_count: GroupConnectionCountMap,
        lands_set_index: LandsSetIndex,
    ) -> None:
        """Handle a standard edge-to-edge terrain connection.

        Args:
            tile_id: Current tile identifier.
            neighbor_id: Adjacent tile identifier.
            initial_side: Cardinal side on current tile before orientation
                mapping.
            cardinal: Effective oriented cardinal side on current tile.
            graph: Mutable graph state.
            tile_def: Current tile definition.
            tiles_info: All tile definitions.
            group_is_linked: Map tracking whether each current group was
                linked.
            group_connection_count: Map counting how many links each group
                formed.
            lands_set_index: Local component lookup index for this add pass.

        Returns:
            None. Mutates component lists and tracking maps when a connection
            exists.
        """
        land, card_grp = self._find_land_and_group_for_side(tile_def, cardinal)
        if land is None or card_grp is None:
            return

        neigh_initial_corner = self.opposite_cardinal.get(initial_side)
        if neigh_initial_corner is None:
            return

        neighbor_vertex = graph.get_vertex(neighbor_id)
        neighbor_def = tiles_info.tiles.get(neighbor_vertex.name.split("/")[0])
        neigh_orientation = neighbor_vertex.get_orientation()
        nx, ny = self.match_matrix.get(neigh_initial_corner)
        neigh_corner = neighbor_def.direction_matrix[neigh_orientation][nx][ny]

        # Check if neighbor has matching terrain on opposite edge
        neighbor_dir_group = self._find_neighbor_group(
            neighbor_def, land, neigh_corner
        )

        if neighbor_dir_group is None:
            return

        # Link current group to existing neighbor component
        existing_set = self._find_component_set(
            land,
            neighbor_id,
            neighbor_dir_group,
            graph,
            lands_set_index,
        )
        if existing_set is None:
            return
        existing_set.append((tile_id, card_grp))
        self._index_set_entry(
            lands_set_index,
            land,
            tile_id,
            card_grp,
            existing_set,
        )
        group_is_linked[tuple(card_grp)] = True
        group_connection_count[tuple(card_grp)] += 1
