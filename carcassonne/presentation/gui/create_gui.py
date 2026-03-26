from carcassonne.presentation.gui.gui import GameGUI
from carcassonne.presentation.gui.game_data_gui import GameDataGui


class CreateGui:
    def __init__(self, game, server, client) -> None:
        game_data = GameDataGui(game, server, client)
        game_gui = GameGUI(game_data)
        game_gui.run()
