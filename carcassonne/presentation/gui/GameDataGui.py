
from carcassonne.presentation.gui import CommandsHandlerGui
from carcassonne.presentation.gui.TilesView import TilesView


class GameDataGui():
    def __init__(self, game):
        self.game = game
        self.nb_tiles = 0               # used to give each drawn tile a unique id
        self.current_tile: TilesView | None = None
        self.current_orientation=0
        self.board_view = None  # set later by Gui
        self.gui = None
        self.is_dragging = False

    def game_configuration(self):
        return self.game.get_game_configuration()

    def new_game(self, players_order, seed):
        """Helper that starts a new game and resets GUI state.

        ``players_order`` and ``seed`` are simply forwarded to the underlying
        game service (``Game.start_new_game``) so callers such as
        :class:`OptionsView` can influence how the match is initialised.
        """
        # the command handler already implements the basic behaviour but it
        # doesn't accept any of the extra keywords, so call the service
        # directly.  ``Game.start_new_game`` is idempotent with respect to
        # shuffling, so we don't need to double‑shuffle here.
        self.game.start_new_game(players_order, seed)
        self.reset()

    def undo(self):
        CommandsHandlerGui.on_undo(self.game)
        if self.board_view:
            self.board_view.refresh()

    def redo(self):
        CommandsHandlerGui.on_redo(self.game)
        if self.board_view:
            self.board_view.refresh()

    def save(self):
        pass
    def load(self):
        pass
    def play_move_gui(self):
        if self.current_tile is None:
            return
        
        final_move = self.current_tile.playable_tile()
        print(final_move)
        result = self.game.play_move(final_move)


        if not self.game.is_undo_history_empty():
                self.game.clear_undo_history()
        if result:
                while self.game.get_current_player().is_ai_player():
                        self.game.play_ai_turn()
        
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
        
        self.current_orientation = (self.current_orientation + 1) % 4
        
        if self.current_tile.move:
            self.current_tile.move = self.current_tile.move[:-1] + str(self.current_orientation)
        
        if self.board_view:
            self.board_view.refresh()
        
        if hasattr(self, 'gui'):
            self.gui.tile_preview.update_rotation()

    def draw_tile(self):
        tile_name = self.game.draw_tile()
        self.nb_tiles += 1
        self.current_tile = TilesView(tile_name, tile_id=self.nb_tiles)
        self.current_orientation = 0
        if self.board_view:
            self.board_view.refresh()
        return tile_name
    
    