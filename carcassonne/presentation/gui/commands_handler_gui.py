from carcassonne.presentation.gui import utils
from gi.repository import Gio, Gtk

"""
Lists of commands that can be triggered from the GUI, and their handlers.
"""

"""
File menu commands:
"""


def on_new(game):
    game.start_new_game()
    game.shuffle_deck()


def on_load(gui) -> None:
    """Show a file picker and load a saved game."""

    dialog = Gtk.FileDialog(title="Load game")

    def on_file_selected(dialog, result):
        try:
            file = dialog.open_finish(result)
            filename = file.get_path()
            if gui.game_data.game.load_game_from_file(filename) == 0:
                # Refresh GUI state after loading
                gui.game_data.reset()
                if hasattr(gui, "players_view"):
                    gui.players_view.refresh()
                if hasattr(gui, "board_view"):
                    gui.board_view.refresh()
                gui.tile_preview.set_filename("")
                gui.window.stack.set_visible_child_name("game")
            else:
                print(f"Failed to load game from {filename}")
        except Exception:
            # Cancelled or failed; ignore.
            pass

    dialog.open(gui.window.window, None, on_file_selected)


def on_save(gui) -> None:
    """Show a file picker and save the current game."""

    dialog = Gtk.FileDialog(title="Save game")

    def on_file_selected(dialog, result):
        try:
            file = dialog.save_finish(result)
            filename = file.get_path()
            if gui.game_data.game.save_game_to_file(filename) == 0:
                print(f"Game saved to {filename}")
            else:
                print(f"Failed to save game to {filename}")
        except Exception:
            # Cancelled or failed; ignore.
            pass

    dialog.save(gui.window.window, None, on_file_selected)


def on_config(gui) -> None:
    config = gui.game_data.game_configuration()
    print("Configuration actuelle du jeu:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    gui.window.stack.set_visible_child_name("options_menu")


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
    gui.game_data.new_game(None, None)
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
    gui.tile_preview.update_rotation()
    gui.update_preview_rotation()


def on_end_turn_gui(gui):
    """Play the pending move and let GameDataGui handle the reset."""
    gui.game_data.play_move_gui()
    # after turn changes, update players list (highlight current player)
    if hasattr(gui, "players_view"):
        gui.players_view.refresh()
