
import re

from carcassonne.presentation.interfaces.i_game_service import IGameService
from carcassonne.datas.starting_tile import initialize_starting_tile_river


class RiverManager():

    def __init__(self, game_data):
        self.game_data = game_data
        self.river_active = False
        self.river_previous_opposite_direction = 0
        self.river_turn = None

    def initialize_river(self) -> None:
        self.river_active = True

    def is_river_active(self) -> bool:
        return self.river_active

    def river_takes_turn(self, turn: int):
        if self.river_turn is not None:
            self.river_previous_opposite_direction = (
                self.river_turn + 2) % 4
        self.river_turn = turn
        print(self.river_previous_opposite_direction)
        print(self.river_turn)

    def check_river_turn(self, move_parts: str):
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
            self.game_data.tiles_info.direction_dict[attach_direction] + 2) % 4

        for i in range(4):
            if tile_lands[(i - orientation) %
                          4] == 'S' and i != already_connected:
                if self.river_turn is not None and i == self.river_previous_opposite_direction:
                    return False
                else:
                    return True
        return True

    def update_river_turn(self, move_parts: str):
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
            self.game_data.tiles_info.direction_dict[attach_direction] + 2) % 4

        for i in range(4):
            if tile_lands[(i - orientation) %
                          4] == 'S' and i != already_connected:
                if self.river_turn is not None and i == self.river_previous_opposite_direction:
                    break
                else:
                    if tile_lands[(i - orientation - 2) % 4] != 'S':
                        self.river_takes_turn(i)
