from carcassonne.Presentation.Gui import utils

"""
Lists of commands that can be triggered from the GUI, and their handlers.
"""

"""
File menu commands:
"""

from carcassonne.Presentation.Gui import utils


def on_new(game):
    game.start_new_game()
    game.shuffle_deck()



def on_load() -> None:
    print("to add load")

def on_save() -> None:
    print("to add save")

def on_config() -> None:
    print("to add config")

def on_info() -> None:
    print("to add info")

def on_quit(self) -> None:
    self.quit()


"""
Game menu commands:
"""

def on_undo(game) -> None:
    game.undo()
    print("to add undo")

def on_redo(game) -> None:
    game.redo()
    print("to add redo")

def on_pause() -> None:
    print("to add pause")

def on_hint():
    print("to add hint")


# GUI-specific commands that operate on the GameGUI instance itself

def on_new_gui(gui):
    """Start a new game and refresh GUI elements."""
    # delegate game logic to GameDataGui
    gui.game_data.new_game()
    # refresh any dependent views
    if hasattr(gui, "players_view"):
        gui.players_view.refresh()
    # clear any tile preview image
    gui.tile_preview.set_filename("")


def on_undo_gui(gui):
    """Undo last move and refresh the board view."""
    gui.game_data.undo()


def on_redo_gui(gui):
    """Redo last undone move and refresh the board view."""
    gui.game_data.redo()


def on_draw_gui(gui):
    """Draw a tile from the deck and update preview."""
    tile = gui.game_data.draw_tile()
    image_path = utils.tile_image_path(tile)
    gui.tile_preview.set_filename(image_path)
    gui.update_preview_rotation()


def on_rotate_gui(gui):
    """Rotate the current tile and refresh preview."""
    gui.game_data.rotate_current_tile()
    gui.update_preview_rotation()


def on_end_turn_gui(gui):
    """Play the pending move and let GameDataGui handle the reset."""
    gui.game_data.play_move_gui()
    # after turn changes, update players list (highlight current player)
    if hasattr(gui, "players_view"):
        gui.players_view.refresh()
