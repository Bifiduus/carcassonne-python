from carcassonne.presentation.gui.BoardView import BoardView
from carcassonne.presentation.gui.Gui import GameGUI
from carcassonne.presentation.gui.GameDataGui import GameDataGui

class CreateGui():
    def __init__(self, game) -> None:
        game_data = GameDataGui(game)
        game_gui= GameGUI(game_data)
        game_gui.run()
