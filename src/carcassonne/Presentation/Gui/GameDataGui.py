
from carcassonne.Presentation.Gui import CommandsHandlerGui
from carcassonne.Presentation.Gui.TilesView import TilesView


class GameDataGui():
    def __init__(self, game):
        self.game = game
        self.nb_tiles = 0               # used to give each drawn tile a unique id
        self.current_tile: TilesView | None = None
        self.current_orientation=0
        self.board_view = None  # set later by Gui
        self.is_dragging = False

    def new_game(self):
        CommandsHandlerGui.on_new(self.game)
        self.reset()

    def undo(self):
        CommandsHandlerGui.on_undo(self.game)
        if self.board_view:
            self.board_view.refresh()

    def redo(self):
        CommandsHandlerGui.on_redo(self.game)
        if self.board_view:
            self.board_view.refresh()

    def play_move_gui(self):
        if self.current_tile is None:
            return
        
        final_move = self.current_tile.playable_tile()
        print(final_move)
        self.game.play_move(final_move)
        self.reset()

    def reset(self):
        self.current_tile = None
        self.current_orientation = 0
        if self.board_view:
            self.board_view.refresh()

    def set_board_view(self, board):
        self.board_view = board

    def rotate_current_tile(self):
        if self.current_tile is None:
            return
        # change orientation state and refresh board
        self.current_orientation = (self.current_orientation + 1) % 4
        if self.board_view:
            self.board_view.refresh()


    def draw_tile(self):
        tile_name = self.game.draw_tile()
        self.nb_tiles += 1
        self.current_tile = TilesView(tile_name, tile_id=self.nb_tiles)
        self.current_orientation = 0
        if self.board_view:
            self.board_view.refresh()
        return tile_name
    