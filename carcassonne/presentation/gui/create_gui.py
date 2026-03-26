from carcassonne.presentation.gui.gui import GameGUI
from carcassonne.presentation.gui.game_data_gui import GameDataGui


class CreateGui:
    def __init__(self, game, server) -> None:
        game_data = GameDataGui(game, server)
        game_gui = GameGUI(game_data)
        game_gui.run()
