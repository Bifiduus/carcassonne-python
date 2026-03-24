
from carcassonne.presentation.interfaces.i_game_service import IGameService
from carcassonne.datas.starting_tile import initialize_starting_tile_river


class RiverManager():

    def __init__(self, game_data):
        self.game_data = game_data
        self.river_active = False

    def initialize_river(self) -> None:
        initialize_starting_tile_river(self.game_data.graph)
        self.river_active = True

    def is_river_active(self) -> bool:
        return self.river_active
