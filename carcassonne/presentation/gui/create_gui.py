from carcassonne.presentation.gui.gui import GameGUI
from carcassonne.presentation.gui.game_data_gui import GameDataGui


class CreateGui:
    def __init__(self, game, client_service, server_service) -> None:
        game_data = GameDataGui(game, client_service, server_service)
        game_gui = GameGUI(game_data)
        game_gui.run()
