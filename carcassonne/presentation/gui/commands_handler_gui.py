from carcassonne.presentation.gui import utils
from gi.repository import Gtk

from carcassonne.i18n import gettext as _

"""
Lists of commands that can be triggered from the GUI, and their handlers.
"""


def _is_game_paused(gui) -> bool:
    return bool(getattr(gui, "is_paused", False))


"""
File menu commands:
"""


def on_new(game):
    game.start_new_game()
    game.shuffle_deck()


def on_load(gui) -> None:
    """Show a file picker and load a saved game."""
    gui.window.window.present()
    dialog = Gtk.FileDialog(title=_("Load game"))

    def on_file_selected(dialog, result):
        try:
            file = dialog.open_finish(result)
            filename = file.get_path()
            river_before = gui.game_data.game_configuration().get(
                "river", False
            )
            if gui.game_data.game.load_game_from_file(filename) == 0:
                river_after = gui.game_data.game_configuration().get(
                    "river", False
                )
                # Re-initialize river_manager with the loaded config
                gui.game_data.game.river_manager.reset()
                if river_after:
                    gui.game_data.game.river_manager.initialize_river()
                # Debug print
                print(
                    "DEBUG: Loaded game with "
                    f"{len(gui.game_data.game.get_board_data())} tiles"
                )
                # Refresh GUI state after loading
                gui.game_data.reset()
                if hasattr(gui, "players_view"):
                    gui.players_view.refresh()
                if hasattr(gui, "board_view"):
                    gui.board_view.refresh()
                gui.tile_preview.set_filename("")
                if hasattr(gui, "set_paused"):
                    gui.set_paused(False)
                gui.window.stack.set_visible_child_name("game")
                # Final refresh of the board after switching to game view
                if hasattr(gui, "board_view"):
                    gui.board_view.refresh()
                # Notify if river mode changed
                if river_before != river_after:
                    if river_after:
                        gui.info_message.show_info(
                            _("River mode has been enabled for this game.")
                        )
                    else:
                        gui.info_message.show_info(
                            _("River mode has been disabled for this game.")
                        )
                # Success message
                gui.info_message.show_info(
                    _("Game successfully loaded from {filename}.").format(
                        filename=filename
                    )
                )
            else:
                gui.error_message.show_error(
                    _("Failed to load the game from {filename}. "
                      "Please check the file format and try again.").format(
                        filename=filename
                    )
                )
        except Exception as e:
            # Check if this is a user cancellation (not an actual error)
            error_msg = str(e).lower()
            if "cancel" in error_msg or "operation was cancelled" in error_msg:
                # User cancelled the dialog; silently ignore
                return
            # Only show error for actual errors, not cancellations
            if hasattr(gui, "error_message"):
                gui.error_message.show_error(
                    _("An error occurred while loading the game: {error}. "
                      "Please try again.").format(error=str(e))
                )

    dialog.open(gui.window.window, None, on_file_selected)


def on_save(gui) -> None:
    """Show a file picker and save the current game."""
    gui.window.window.present()
    dialog = Gtk.FileDialog(title=_("Save game"))

    def on_file_selected(dialog, result):
        try:
            file = dialog.save_finish(result)
            filename = file.get_path()
            if gui.game_data.game.save_game_to_file(filename) == 0:
                gui.info_message.show_info(
                    _("Game successfully saved to {filename}.").format(
                        filename=filename
                    )
                )
            else:
                if hasattr(gui, "error_message"):
                    gui.error_message.show_error(
                        _("Failed to save the game to {filename}. "
                          "Please check the file path and try again.").format(
                            filename=filename
                        )
                    )
        except Exception as e:
            # Check if this is a user cancellation (not an actual error)
            error_msg = str(e).lower()
            if "cancel" in error_msg or "operation was cancelled" in error_msg:
                # User cancelled the dialog; silently ignore
                return
            # Only show error for actual errors, not cancellations
            if hasattr(gui, "error_message"):
                gui.error_message.show_error(
                    _("An error occurred while saving the game: {error}. "
                      "Please try again.").format(error=str(e))
                )

    dialog.save(gui.window.window, None, on_file_selected)


def on_config(gui) -> None:
    config = gui.game_data.game_configuration()
    print(_("Current game configuration:"))
    for key, value in config.items():
        print(f"  {key}: {value}")
    gui.window.stack.set_visible_child_name("singleplayer_menu")


def on_info(gui) -> None:
    import carcassonne

    message = """Carcassonne Python

Version: {carcassonne.__version__}

{authors_label}:
- Clément SIMON --- Server
- Maxence SALIN --- Client GUI/CLI
- Loic THIN --- AI and game logic
- Anthony BEAUVIEUX --- Game logic
- Tony HUANG --- Seed, shuffle and game logic
"""
    message = message.format(
        carcassonne=carcassonne,
        authors_label=_("Authors"),
    )
    gui.info_message.show_info(message)


def on_quit(self) -> None:
    self.quit()


"""
Game menu commands:
"""


def on_undo(game) -> None:
    game.undo()


def on_redo(game) -> None:
    game.redo()


def on_pause(gui=None) -> None:
    if gui is not None and hasattr(gui, "toggle_pause"):
        gui.toggle_pause()
        return
    print(_("Pause is not implemented yet."))


def on_hint(gui):
    """Provide a hint for the current position."""
    if _is_game_paused(gui):
        return

    # Check preconditions in presentation layer
    if hasattr(gui, "game_data") and hasattr(gui.game_data, "game"):
        if gui.game_data.game.game_data.current_hand is None:
            if hasattr(gui, "error_message"):
                gui.error_message.show_error(
                    _("You must draw a tile before requesting a hint. "
                      "Please draw a tile first and then try again.")
                )
            return

    gui.game_data.provide_hint()


# GUI-specific commands that operate on the GameGUI instance itself


def on_new_gui(gui):
    """Start a new game and refresh GUI elements."""
    if hasattr(gui, "set_paused"):
        gui.set_paused(False)
    # delegate game logic to GameDataGui
    gui.game_data.new_game(None, None)
    # refresh any dependent views
    if hasattr(gui, "players_view"):
        gui.players_view.refresh()
    # clear any tile preview image
    gui.tile_preview.set_filename("")


def on_undo_gui(gui):
    """Undo last move and refresh the board view."""
    if _is_game_paused(gui):
        return

    # Check preconditions in presentation layer
    if hasattr(gui, "game_data") and hasattr(gui.game_data, "game"):
        history = getattr(gui.game_data.game.game_data, "history", None)
        past_moves = getattr(history, "past_moves", []) if history else []
        if not past_moves:
            if hasattr(gui, "error_message"):
                gui.error_message.show_error(
                    _(
                        "There are no moves to undo. "
                        "You need to play at least one move before "
                        "you can undo."
                    )
                )
            return
    gui.game_data.undo()


def on_redo_gui(gui):
    """Redo last undone move and refresh the board view."""
    if _is_game_paused(gui):
        return

    # Check preconditions in presentation layer
    if hasattr(gui, "game_data") and hasattr(gui.game_data, "game"):
        history = getattr(gui.game_data.game.game_data, "history", None)
        future_moves = getattr(history, "future_moves", []) if history else []
        if not future_moves:
            if hasattr(gui, "error_message"):
                gui.error_message.show_error(
                    _(
                        "There are no moves to redo. "
                        "You need to undo a move before you can redo."
                    )
                )
            return
    gui.game_data.redo()


def on_draw_gui(gui):
    """Draw a tile from the deck and update preview."""
    if _is_game_paused(gui):
        return

    tile = gui.game_data.draw_tile()
    if tile is None:
        # Provide specific error message based on context
        error_msg = None
        if hasattr(gui, "game_data") and hasattr(gui.game_data, "game"):
            if gui.game_data.game.game_data.current_hand is not None:
                error_msg = _(
                    "You already have a tile in hand. "
                    "You must play it or undo your move before drawing "
                    "a new tile."
                )
            elif gui.game_data.game.game_data.deck.is_empty():
                error_msg = _(
                    "The deck is empty. "
                    "All tiles have been drawn. No more tiles are "
                    "available to draw."
                )

        if error_msg is None:
            error_msg = _(
                "The tile could not be drawn. "
                "Please check if it is your turn and try again."
            )

        gui.tile_preview.set_filename("")
        if hasattr(gui, "error_message"):
            gui.error_message.show_error(error_msg)
        if hasattr(gui, "players_view"):
            gui.players_view.refresh()
        return
    image_path = utils.tile_image_path(tile)
    gui.tile_preview.set_filename(image_path)
    gui.update_preview_rotation()


def on_rotate_gui(gui):
    """Rotate the current tile and refresh preview."""
    if _is_game_paused(gui):
        return

    # Check preconditions in presentation layer
    if hasattr(gui, "game_data") and hasattr(gui.game_data, "game"):
        if gui.game_data.game.game_data.current_hand is None:
            if hasattr(gui, "error_message"):
                gui.error_message.show_error(
                    _("You must draw a tile before rotating. "
                      "Please draw a tile first and then try again.")
                )
            return

    gui.game_data.rotate_current_tile()
    gui.tile_preview.update_rotation()
    gui.update_preview_rotation()


def on_end_turn_gui(gui):
    """Play the pending move and let GameDataGui handle the reset."""
    if _is_game_paused(gui):
        return

    # Check preconditions in presentation layer
    if (
        hasattr(gui.game_data, "current_tile")
        and gui.game_data.current_tile is None
    ):
        if hasattr(gui, "error_message"):
            gui.error_message.show_error(
                _("No tile has been placed on the board. "
                  "Please select a tile placement location and try again.")
            )
        return

    if hasattr(gui, "game_data") and hasattr(gui.game_data, "game"):
        if gui.game_data.game.game_data.current_hand is None:
            if hasattr(gui, "error_message"):
                gui.error_message.show_error(
                    _("You must draw a tile before playing a move. "
                      "Please draw a tile first and then try again.")
                )
            return

    gui.game_data.play_move_gui()
    # after turn changes, update players list (highlight current player)
    if hasattr(gui, "players_view"):
        gui.players_view.refresh()
