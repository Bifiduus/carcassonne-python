
from carcassonne.presentation.interfaces.i_game_service import IGameService


class River(IGameService):

    def __init__(self, game_data):
        self.game_data = game_data
