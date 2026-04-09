import re


class RiverManager:
    """Manage the river tile sequence and its directional constraints.

    During a river game the first tiles placed must follow a contiguous river.
    This manager tracks whether the river is still active, the orientation of
    the last river tile placed, and enforces the rule that the river cannot
    immediately reverse direction (U-turn).
    """

    def __init__(self, game_data):
        self.game_data = game_data
        # True while river tiles are still being placed (before the lake tile).
        self.river_active = False
        # The compass index (0-3) opposite to the last river segment direction.
        # Used to prevent immediate U-turns.
        self.river_previous_opposite_direction = 0
        # Compass index of the outgoing river side of the last river tile placed.
        self.river_turn = None

    def initialize_river(self) -> None:
        self.river_active = True
        self.river_previous_opposite_direction = 0
        self.river_turn = None

    def reset(self) -> None:
        self.river_active = False
        self.river_previous_opposite_direction = 0
        self.river_turn = None

    def is_river_active(self) -> bool:
        return self.river_active

    def river_takes_turn(self, turn: int):
        """Record that the river flows outward in direction ``turn``.

        Updates ``river_previous_opposite_direction`` so the next tile cannot
        immediately reverse the river back on itself.

        Args:
            turn: Compass index (0=N, 1=E, 2=S, 3=W) of the outgoing river side.
        """
        if self.river_turn is not None:
            self.river_previous_opposite_direction = (self.river_turn + 2) % 4
        self.river_turn = turn

    def check_river_turn(self, move_parts: str):
        """Return True if the proposed river tile placement is directionally valid.

        Checks that the tile's outgoing river side does not produce a U-turn
        (i.e. it must not flow back into the direction the river came from).

        Args:
            move_parts: The move string already split on ``"/"``
                        (e.g. ``["FSRS", "0N1"]``).

        Returns:
            True if the river direction is acceptable, False for a U-turn.
        """
        tile_lands = move_parts[0]
        counter = 1
        if len(move_parts[counter]) == 1:
            counter = 2
        integers_placement = [
            int(x) for x in re.findall(r"\d+", move_parts[counter])
        ]
        attach_direction = "".join(
            c for c in move_parts[counter] if c.isalpha()
        )
        orientation = integers_placement[1]

        already_connected = (
            self.game_data.tiles_info.direction_dict[attach_direction] + 2
        ) % 4

        for i in range(4):
            if tile_lands[(i - orientation) %
                          4] == 'S' and i != already_connected:
                if (self.river_turn is not None
                        and i == self.river_previous_opposite_direction):
                    return False
                else:
                    return True
        return True

    def update_river_turn(self, move_parts: str):
        """Persist the new river direction after a valid tile has been placed.

        Should be called once ``check_river_turn`` has returned True and the
        tile is committed to the board.

        Args:
            move_parts: The move string already split on ``"/"``
                        (e.g. ``["FSRS", "0N1"]``).
        """
        tile_lands = move_parts[0]
        counter = 1
        if len(move_parts[counter]) == 1:
            counter = 2
        integers_placement = [
            int(x) for x in re.findall(r"\d+", move_parts[counter])
        ]
        attach_direction = "".join(
            c for c in move_parts[counter] if c.isalpha()
        )
        orientation = integers_placement[1]

        already_connected = (
            self.game_data.tiles_info.direction_dict[attach_direction] + 2
        ) % 4

        for i in range(4):
            if tile_lands[(i - orientation) %
                          4] == 'S' and i != already_connected:
                if (self.river_turn is not None
                        and i == self.river_previous_opposite_direction):
                    break
                else:
                    if tile_lands[(i - orientation - 2) % 4] != "S":
                        self.river_takes_turn(i)
