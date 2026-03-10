from carcassonne.Presentation.Gui.BoardView import BoardView
from carcassonne.Presentation.Gui.Gui import GameGUI
from carcassonne.Presentation.Gui.GameDataGui import GameDataGui

class CreateGui():
    def __init__(self, game) -> None:
        game_data = GameDataGui(game)
        game_gui= GameGUI(game_data)
        game_gui.run()
