"""Rule checks for Carcassonne moves.

RulesManager validates move format, legality, and meeple placement based on
the current graph and tile definitions.
"""

import copy
import re
from carcassonne.business_logic.game.river_manager import RiverManager
from carcassonne.business_logic.interfaces.i_graph_data import IGraphData
from carcassonne.business_logic.interfaces.i_tiles_info import ITilesInfo
from carcassonne.business_logic.graph_logic import GraphLogic
from carcassonne.datas.tiles_constants import MATCH_MATRIX
from carcassonne.datas.tiles_constants import OPPOSITE_SIDE_MATRIX
from carcassonne.datas.tiles_info import Tile


class RulesManager:

    opposite_side_matrix = OPPOSITE_SIDE_MATRIX

    match_matrix = MATCH_MATRIX

    def __init__(self, tiles_info: ITilesInfo):
        """Initialize RulesManager.

        Args:
            tiles_info: Tile definitions and metadata for move validation.

        Returns:
            None.
        """
        self.tiles_info = tiles_info
        self._graph_logic = None

    def _get_graph_logic(self) -> GraphLogic:
        """Retrieve or initialize the shared GraphLogic instance.

        Uses lazy initialization to avoid repeated object allocation during
        move validation.

        Args:
            None.

        Returns:
            Shared GraphLogic instance.
        """
        if self._graph_logic is None:
            self._graph_logic = GraphLogic()
        return self._graph_logic

    @staticmethod
    def _extract_placement_data(placement_info: str) -> tuple[list[int], str]:
        """Parse placement specification into numeric tile ID, orientation.

        Extracts integers and cardinal direction letters from a placement
        specification string.

        Args:
            placement_info: Placement spec (e.g. "12N" for tile 12, side N).

        Returns:
            Tuple of ([tile_id, orientation], direction_letters).
        """
        placement_numbers = [
            int(x) for x in re.findall(r"\d+", placement_info)
        ]
        target_side = "".join(c for c in placement_info if c.isalpha())
        return placement_numbers, target_side

    @staticmethod
    def _find_component_set_name(
        graph: IGraphData,
        land_type: str,
        tile_id: int,
        land_pos: str,
    ) -> str | None:
        """Locate which component set contains a specific tile position.

        Searches for the named component containing a given tile and position.

        Args:
            graph: Current graph state with components.
            land_type: Terrain type key (e.g., "R", "C", "M", "S").
            tile_id: Tile identifier to search for.
            land_pos: Position on the tile (e.g., "N", "C", "SE").

        Returns:
            Component set name (e.g., "R2") if found, otherwise None.
        """
        lands = graph.lands_components.get(land_type, {})
        for set_name, component_set in lands.items():
            for tile_id_in_set, directions in component_set:
                if tile_id_in_set == tile_id and land_pos in directions:
                    return set_name
        return None

    def can_place_meeple_on_tile_side(
        self,
        move_parts: list[str],
        counter: int,
        graph: IGraphData,
        current_player_id: int | None = None,
    ) -> bool:
        """Validate meeple placement by simulating placement in isolated graph.

        Tests whether placing a meeple on the target component would cause a
        conflict with existing meeples. Uses a simulated placement to avoid
        mutating the live game state.

        Args:
            move_parts: Parsed move components.
                ([tile_code, center?, placement, meeple]).
            counter: Index in move_parts for meeple placement position.
            graph: Current game graph.
            current_player_id: Player placing the meeple (optional,
                overrides conflict).

        Returns:
            True if meeple placement is valid, False otherwise.
        """
        tile_code = move_parts[0]
        side_placement = move_parts[counter]
        placement_info = move_parts[counter - 1]
        placement_numbers, target_side = self._extract_placement_data(
            placement_info
        )
        # Early read-only check: get tile position without copying graph.
        tile_pos = graph.get_adjacent_position(
            vertex_id=placement_numbers[0],
            side=self.tiles_info.direction_dict[target_side],
        )
        if tile_pos is None:
            return False
        # Use an isolated copy so rule checks do not mutate the live game
        # state (land components, vertices, meeples, etc.).
        graph_copy = copy.deepcopy(graph)
        turn = max(graph_copy.get_vertices().keys(), default=-1) + 1
        new_tile_id = turn
        graph_copy.add_vertex(
            vertex_id=turn,
            name=tile_code,
            middle=move_parts[1] if counter == 3 else "",
            orientation=placement_numbers[1],
            position=tile_pos,
        )
        graph_logic = self._get_graph_logic()
        graph_logic.add_lands_components(
            tile_id=new_tile_id,
            graph=graph_copy,
            tiles_info=self.tiles_info,
        )
        vertex = graph_copy.get_vertex(new_tile_id)
        land_matrix = vertex.get_matrix()
        land_type = land_matrix[self.match_matrix[side_placement][0]][
            self.match_matrix[side_placement][1]
        ]
        if land_type == "S":
            graph_copy.remove_vertex(new_tile_id)
            return False
        if not land_type or land_type not in graph_copy.lands_components:
            graph_copy.remove_vertex(new_tile_id)
            return False
        land_pos = Tile.direction_matrix[placement_numbers[1]][
            self.match_matrix[side_placement][0]
        ][self.match_matrix[side_placement][1]]
        component_set_name = self._find_component_set_name(
            graph_copy,
            land_type,
            new_tile_id,
            land_pos,
        )
        if component_set_name is None:
            graph_copy.remove_vertex(new_tile_id)
            return False
        for meeple in graph_copy.get_meeples():
            if meeple.lands_components == component_set_name:
                if (
                    current_player_id is not None
                    and meeple.player_id == current_player_id
                ):
                    continue
                graph_copy.remove_vertex(new_tile_id)
                return False
        graph_copy.remove_vertex(new_tile_id)
        return True

    def explain_meeple_placement_failure(
        self,
        move_parts: list[str],
        counter: int,
        graph: IGraphData,
        current_player_id: int | None = None,
    ) -> str:
        """Return a human-readable reason for an invalid meeple placement."""
        tile_code = move_parts[0]
        side_placement = move_parts[counter]
        placement_info = move_parts[counter - 1]
        placement_numbers, target_side = self._extract_placement_data(
            placement_info
        )
        tile_pos = graph.get_adjacent_position(
            vertex_id=placement_numbers[0],
            side=self.tiles_info.direction_dict[target_side],
        )
        if tile_pos is None:
            return "target tile position is invalid"

        graph_copy = copy.deepcopy(graph)
        new_tile_id = max(graph_copy.get_vertices().keys(), default=-1) + 1
        graph_copy.add_vertex(
            vertex_id=new_tile_id,
            name=tile_code,
            middle=move_parts[1] if counter == 3 else "",
            orientation=placement_numbers[1],
            position=tile_pos,
        )
        graph_logic = self._get_graph_logic()
        graph_logic.add_lands_components(
            tile_id=new_tile_id,
            graph=graph_copy,
            tiles_info=self.tiles_info,
        )
        vertex = graph_copy.get_vertex(new_tile_id)
        if vertex is None:
            return "target tile could not be simulated"

        side_x, side_y = self.match_matrix[side_placement]
        land_type = vertex.get_matrix()[side_x][side_y]
        if land_type == "S":
            graph_copy.remove_vertex(new_tile_id)
            return "meeples cannot be placed on river segments"
        if not land_type or land_type not in graph_copy.lands_components:
            graph_copy.remove_vertex(new_tile_id)
            return (
                "selected meeple position does not belong"
                " to a valid component"
            )

        land_pos = Tile.direction_matrix[placement_numbers[1]][side_x][side_y]
        component_set_name = self._find_component_set_name(
            graph_copy,
            land_type,
            new_tile_id,
            land_pos,
        )
        if component_set_name is None:
            graph_copy.remove_vertex(new_tile_id)
            return "selected meeple position does not map to a component"

        for meeple in graph_copy.get_meeples():
            if meeple.lands_components == component_set_name:
                if (
                    current_player_id is not None
                    and meeple.player_id == current_player_id
                ):
                    continue
                graph_copy.remove_vertex(new_tile_id)
                return (
                    f"component {component_set_name} already contains a meeple"
                )

        graph_copy.remove_vertex(new_tile_id)
        return "meeple placement is invalid"

    def are_equal_sides(
        self,
        tile1: list[str],
        tile1pos: tuple[int, int],
        orientation: int,
        graph: IGraphData,
        river_manager: RiverManager,
    ) -> bool:
        """Check if terrain sides match between new tile and neighbor tiles.

        Validates that the new tile's edges align with existing neighbors.
        Handles river rules when active.

        Args:
            tile1: New tile being placed (land matrix edges).
            tile1pos: Board position of the new tile.
            orientation: Rotation applied to tile1 (0-3).
            graph: Current game graph with placed neighbors.
            river_manager: River state and validation rules.

        Returns:
            True if all matching sides are equal, False otherwise.
        """
        consider_river_rules = river_manager.is_river_active()
        is_river_over = river_manager.game_data.is_river_over()
        river_checked = False

        # Build position->vertex dict once to enable O(1) lookups per neighbor.
        # More efficient than scanning all vertices for each of 4 directions.
        vertices_by_position = {
            vertex.get_position(): vertex
            for vertex in graph.get_vertices().values()
        }

        for direction_index in range(4):
            next_pos = graph.get_adjacent_position_from(
                tile1pos, direction_index
            )
            neighbor_vertex = vertices_by_position.get(next_pos)
            if neighbor_vertex is None:
                continue

            tile2 = neighbor_vertex.get_matrix()
            land1 = tile1[(direction_index - orientation) % 4]
            tile2_coord = self.opposite_side_matrix[direction_index]
            land2 = tile2[tile2_coord[0]][tile2_coord[1]]

            if land1 != land2:
                return False

            if consider_river_rules and land1 == "S":
                river_checked = True

        if consider_river_rules and not is_river_over and not river_checked:
            return False

        return True

    def is_legal_move(
        self,
        move_parts: list[str],
        graph: IGraphData,
        river_manager: RiverManager,
        current_player_id: int | None = None,
    ) -> bool:
        """Verify move legality: availability, placement, and game rules.

        Checks that the tile is available, can be placed at the target
        position, sides match neighbors, river rules are satisfied, and
        meeples are legal.

        Args:
            move_parts: Parsed move components.
            graph: Current game graph.
            river_manager: River placement validator.
            current_player_id: Player ID for meeple conflict checks (optional).

        Returns:
            True if the move is legal, False otherwise.
        """
        part_index = 0

        part_index += 1
        if len(move_parts[part_index]) == 1:
            if not self.tiles_info.is_tile_left(
                move_parts[part_index - 1] + "/" + move_parts[part_index]
            ):
                return False
            part_index += 1
        else:
            if not self.tiles_info.is_tile_left(move_parts[part_index - 1]):
                return False

        placement_numbers, target_side = self._extract_placement_data(
            move_parts[part_index]
        )

        if not graph.get_vertices()[placement_numbers[0]].is_neighbor_free(
            self.tiles_info.direction_dict[target_side]
        ):
            return False

        tile_pos = graph.get_adjacent_position(
            placement_numbers[0],
            self.tiles_info.direction_dict[target_side],
        )
        if not self.are_equal_sides(
            move_parts[0],
            tile_pos,
            placement_numbers[1],
            graph,
            river_manager,
        ):
            return False

        # Check river extension rules: stream direction continuity and
        # placement validity.
        if not river_manager.check_river_turn(move_parts):
            return False

        part_index += 1
        if len(move_parts) - 1 == part_index:
            if not self.can_place_meeple_on_tile_side(
                move_parts,
                part_index,
                graph,
                current_player_id,
            ):
                return False

        return True

    def is_correctly_formed_move(self, move: str, graph: IGraphData) -> bool:
        """Verify move format and syntax compliance.

        Checks string format, part count, tile availability, placement syntax,
        and meeple placement validity without checking game state legality.

        Args:
            move: Move string with format "tile[/center]/placement[/meeple]".
            graph: Current game graph (used for tile ID validation).

        Returns:
            True if the move is correctly formed, False otherwise.
        """

        part_index = 0
        if not isinstance(move, str):
            return False

        move_parts = move.split("/")
        if not 2 <= len(move_parts) <= 4:
            return False
        if move_parts[part_index] not in self.tiles_info.tiles_dict:
            return False

        part_index += 1
        if len(move_parts[part_index]) == 1:
            if (
                move_parts[part_index]
                not in self.tiles_info.tiles_dict[move_parts[part_index - 1]]
            ):
                return False
            part_index += 1
        else:
            if (
                "void"
                not in self.tiles_info.tiles_dict[move_parts[part_index - 1]]
            ):
                return False

        if len(move_parts) <= part_index:
            return False

        placement_numbers, target_side = self._extract_placement_data(
            move_parts[part_index]
        )
        if len(placement_numbers) != 2:
            return False
        if (
            placement_numbers[0]
            >= max(graph.get_vertices().keys(), default=-1) + 1
        ):
            return False
        if len(target_side) != 1:
            return False
        if target_side not in self.tiles_info.direction_list:
            return False
        if not (0 <= placement_numbers[1] <= 3):
            return False

        part_index += 1
        if len(move_parts) - 1 == part_index:
            if move_parts[part_index] not in (
                self.tiles_info.meeple_placement_list
            ):
                return False

        return True

    def check_move(
        self,
        move: str,
        graph: IGraphData,
        river_manager: RiverManager,
        current_player_id: int | None = None,
    ) -> bool:
        """Perform complete move validation (format + legality).

        Wraps `is_correctly_formed_move()` and `is_legal_move()` for full
        validation in a single call.

        Args:
            move: Move string to validate.
            graph: Current game graph.
            river_manager: River placement validator.
            current_player_id: Player ID (optional).

        Returns:
            True if the move is valid, False otherwise.
        """
        if not self.is_correctly_formed_move(move, graph=graph):
            return False

        if not self.is_legal_move(
            move.split("/"), graph, river_manager, current_player_id
        ):
            return False

        return True

    def explain_invalid_move(
        self,
        move: str,
        graph: IGraphData,
        river_manager: RiverManager,
        current_player_id: int | None = None,
    ) -> str:
        """Return a human-readable reason explaining why a move is invalid."""
        if not isinstance(move, str):
            return "move must be a string"

        move_parts = move.split("/")
        part_index = 0
        if not 2 <= len(move_parts) <= 4:
            return "move format is invalid"
        if move_parts[part_index] not in self.tiles_info.tiles_dict:
            return "tile code is invalid"

        part_index += 1
        if len(move_parts[part_index]) == 1:
            if (
                move_parts[part_index]
                not in self.tiles_info.tiles_dict[move_parts[part_index - 1]]
            ):
                return "tile center variant is invalid"
            tile_identifier = (
                move_parts[part_index - 1] + "/" + move_parts[part_index]
            )
            part_index += 1
        else:
            if (
                "void"
                not in self.tiles_info.tiles_dict[move_parts[part_index - 1]]
            ):
                return "tile center variant is missing"
            tile_identifier = move_parts[part_index - 1]

        if len(move_parts) <= part_index:
            return "move placement is missing"

        placement_numbers, target_side = self._extract_placement_data(
            move_parts[part_index]
        )
        if len(placement_numbers) != 2:
            return "placement format is invalid"
        max_id = max(graph.get_vertices().keys(), default=-1) + 1
        if placement_numbers[0] >= max_id:
            return "target tile id does not exist"
        if (
            len(target_side) != 1
            or target_side not in self.tiles_info.direction_list
        ):
            return "target side is invalid"
        if not (0 <= placement_numbers[1] <= 3):
            return "tile rotation is invalid"

        if len(move_parts) - 1 == part_index + 1:
            if (
                move_parts[part_index + 1]
                not in self.tiles_info.meeple_placement_list
            ):
                return "meeple position is invalid"

        if not self.tiles_info.is_tile_left(tile_identifier):
            return f"tile {tile_identifier} is not available"

        target_vertex = graph.get_vertices().get(placement_numbers[0])
        if target_vertex is None:
            return "target tile id does not exist"
        if not target_vertex.is_neighbor_free(
            self.tiles_info.direction_dict[target_side]
        ):
            return "target side is already occupied"

        tile_pos = graph.get_adjacent_position(
            placement_numbers[0],
            self.tiles_info.direction_dict[target_side],
        )
        if not self.are_equal_sides(
            move_parts[0],
            tile_pos,
            placement_numbers[1],
            graph,
            river_manager,
        ):
            return "tile sides do not match neighboring tiles"

        if not river_manager.check_river_turn(move_parts):
            return "river placement rules are violated"

        meeple_present = len(move_parts) - 1 == part_index + 1
        if meeple_present and not self.can_place_meeple_on_tile_side(
            move_parts,
            part_index + 1,
            graph,
            current_player_id,
        ):
            return self.explain_meeple_placement_failure(
                move_parts,
                part_index + 1,
                graph,
                current_player_id,
            )

        return "move is invalid"
