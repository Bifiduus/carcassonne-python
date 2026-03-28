from gi.repository import GLib, Gtk, Gio, Gdk, GdkPixbuf

from carcassonne.presentation.gui import commands_handler_gui
from carcassonne.presentation.gui.board_view import BoardView
from carcassonne.presentation.gui.error_message_view import ErrorMessageView
from carcassonne.presentation.gui.info_message import InfoMessage
from carcassonne.presentation.gui.menus.ai_menu import AiMenu
from carcassonne.presentation.gui.menus.keybinds_menu import KeybindsMenu
from carcassonne.presentation.gui.window_view import WindowView
from carcassonne.presentation.gui import utils
from carcassonne.presentation.gui.menus.main_menu import MainMenu
from carcassonne.presentation.gui.tile_preview import TilePreview
from carcassonne.presentation.gui.players_view import PlayersView
from carcassonne.presentation.gui.menus.singleplayer_menu import (
    SingleplayerMenu,
)
from carcassonne.presentation.gui.menus.options_menu import OptionsMenu


import gi

gi.require_version("Gtk", "4.0")


class GameGUI(Gtk.Application):
    """Top level application class for the GTK GUI.

    Most of the messy initialization logic that used to live in this file is
    now delegated to small helper modules.  This keeps ``GameGUI``
    responsibilities focused on gluing things together rather than building
    buttons and menus itself.
    """

    def __init__(self, game_data):
        super().__init__(application_id="com.example.Carcassonne", flags=0)
        GLib.set_application_name("Carcassonne")

        self.game_data = game_data
        self.running = True

        # global CSS and shared helpers
        utils.load_css()

        # simple controls used in the overlay; the handlers delegate to the
        # command module directly so the GUI doesn't need to know game logic.
        self.button_draw = Gtk.Button(label="Draw Tile (t)")
        self.button_draw.connect(
            "clicked", lambda b: commands_handler_gui.on_draw_gui(self)
        )

        self.button_end_turn = Gtk.Button(label="End Turn (space)")
        self.button_end_turn.connect(
            "clicked", lambda b: commands_handler_gui.on_end_turn_gui(self)
        )
        self.error_message = ErrorMessageView(self)
        self.info_message = InfoMessage(self)

    def do_activate(self):
        window = WindowView(self, self.game_data)
        self.window = window
        # self.error_message.show_error("Welcome to Carcassonne!")

        # main menu is now produced by a small helper
        menu_overlay = Gtk.Overlay()

        # 📸 Background
        background = Gtk.Picture.new_for_filename(
            utils.get_images_dir() + "/main_menu_background_test.png"
        )
        background.set_can_shrink(True)
        background.set_keep_aspect_ratio(False)

        menu_overlay.set_child(background)

        # 📦 Ton menu actuel
        menu = MainMenu.create(self)

        menu_overlay.add_overlay(menu)

        # 👉 on met l'overlay dans le stack
        window.stack.add_named(menu_overlay, "menu")

        # options page is built once and kept around so that the user can
        # revisit it from either the *Options* button or after doing a
        # multi-player game later on.
        self.singleplayer_options_view = SingleplayerMenu(self)
        window.stack.add_named(
            self.singleplayer_options_view, "singleplayer_menu"
        )
        self.options_view = OptionsMenu(self)
        window.stack.add_named(self.options_view, "options_menu")
        self.keybinds_view = KeybindsMenu(self)
        window.stack.add_named(self.keybinds_view, "keybinds_menu")
        self.ai_view = AiMenu(self)
        window.stack.add_named(self.ai_view, "ai_menu")

        # register actions used by the menus and shortcuts
        register = utils.register_action
        register(
            self, "new", lambda a, p: commands_handler_gui.on_new_gui(self)
        )
        register(self, "load", lambda a, p: commands_handler_gui.on_load(self))
        register(self, "save", lambda a, p: commands_handler_gui.on_save(self))
        register(
            self, "config", lambda a, p: commands_handler_gui.on_config(self)
        )
        register(self, "info", lambda a, p: commands_handler_gui.on_info(self))
        register(self, "quit", lambda a, p: commands_handler_gui.on_quit(self))
        register(
            self, "undo", lambda a, p: commands_handler_gui.on_undo_gui(self)
        )
        register(
            self, "redo", lambda a, p: commands_handler_gui.on_redo_gui(self)
        )
        register(self, "pause", lambda a, p: commands_handler_gui.on_pause())
        register(self, "hint", lambda a, p: commands_handler_gui.on_hint(self))

        # the ``WindowView`` helper already attaches the file/game menus; an
        # explicit quit action is duplicated here for safety.
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect(
            "activate", lambda a, p: commands_handler_gui.on_quit(self)
        )
        self.add_action(quit_action)

        # ----------- game overlay (board + controls) -----------------------
        overlay = Gtk.Overlay()

        self.board_view = BoardView(self.game_data)
        self.game_data.set_board_view(self.board_view)
        self.game_data.gui = self
        overlay.set_child(self.board_view)

        # show player list at top-left corner
        self.players_view = PlayersView(self.game_data)
        self.players_view.add_css_class("players-panel")
        overlay.add_overlay(self.players_view)

        # back button in top-right corner
        back_button = Gtk.Button(label="Back to Menu")
        back_button.set_margin_top(10)
        back_button.set_margin_end(10)
        back_button.set_halign(Gtk.Align.END)
        back_button.set_valign(Gtk.Align.START)
        back_button.add_css_class("back-buttons")
        back_button.connect(
            "clicked",
            lambda b: self.window.stack.set_visible_child_name("menu"),
        )
        overlay.add_overlay(back_button)

        # end-turn button in a semi-transparent panel
        end_turn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        end_turn_box.set_margin_bottom(40)
        end_turn_box.set_halign(Gtk.Align.CENTER)
        end_turn_box.set_valign(Gtk.Align.END)
        end_turn_box.add_css_class("end-turn-panel")
        end_turn_box.append(self.button_end_turn)

        # corner panel contains the tile preview and draw button
        corner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        corner_box.set_margin_end(15)
        corner_box.set_margin_bottom(15)
        corner_box.set_halign(Gtk.Align.END)
        corner_box.set_valign(Gtk.Align.END)
        corner_box.add_css_class("corner-panel")

        self.tile_preview = TilePreview(self)
        corner_box.append(self.tile_preview)
        corner_box.append(self.button_draw)

        overlay.add_overlay(corner_box)
        overlay.add_overlay(end_turn_box)

        # application shortcuts for the three game actions
        register(
            self, "draw", lambda a, p: commands_handler_gui.on_draw_gui(self)
        )
        self.set_accels_for_action("app.draw", ["t"])
        register(
            self,
            "rotate",
            lambda a, p: commands_handler_gui.on_rotate_gui(self),
        )
        self.set_accels_for_action("app.rotate", ["r"])
        register(
            self,
            "end_turn",
            lambda a, p: commands_handler_gui.on_end_turn_gui(self),
        )
        self.set_accels_for_action("app.end_turn", ["space"])

        window.stack.add_named(overlay, "game")
        window.stack.set_visible_child_name("menu")

        self.background_image = "fond_bois.jpg"
        self.board_view.set_background(
            utils.get_images_dir() + "/" + self.background_image
        )

        # make the window visible on screen
        window.window.present()
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self._on_global_key_press)
        window.window.add_controller(key_controller)

    def _on_global_key_press(self, controller, keyval, keycode, state):
        self.window.hide_menus()
        if keyval == Gdk.KEY_r:
            commands_handler_gui.on_rotate_gui(self)
            return True
        return False

    def on_end_turn(self, action, param):
        # kept for backward compatibility; newer code should use
        # commands_handler_gui
        commands_handler_gui.on_end_turn_gui(self)

    def on_rotate(self, action, param):
        commands_handler_gui.on_rotate_gui(self)

    def on_preview_pressed(self, gesture, n_press, x, y):
        self.game_data.is_dragging = True
        self.board_view.grab_focus()
        self.game_data.refresh()

    def on_preview_released(self, gesture, n_press, x, y):
        self.game_data.is_dragging = False
        self.game_data.refresh()

    def start_singleplayer(self, button):
        # self.game.start_new_game(mode="single")
        self.window.stack.set_visible_child_name("game")
        commands_handler_gui.on_new_gui(self)
        self.board_view.grab_focus()

    def start_multiplayer(self, button):
        # self.game.start_new_game(mode="multi")
        self.window.stack.set_visible_child_name("game")

    def show_options(self, button):
        self.window.stack.set_visible_child_name("options_menu")

    def on_draw(self, action, param):
        # legacy entry point; forward to handler
        commands_handler_gui.on_draw_gui(self)

    def update_preview_rotation(self):
        if not self.game_data.current_tile:
            return

        image_path = utils.tile_image_path(
            self.game_data.current_tile.current_tile
        )

        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=image_path,
            width=100,
            height=100,
            preserve_aspect_ratio=True,
        )

        # Rotate pixbuf
        rotated = pixbuf.rotate_simple(
            [
                GdkPixbuf.PixbufRotation.NONE,
                GdkPixbuf.PixbufRotation.CLOCKWISE,
                GdkPixbuf.PixbufRotation.UPSIDEDOWN,
                GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE,
            ][self.game_data.current_orientation]
        )

        texture = Gdk.Texture.new_for_pixbuf(rotated)
        self.tile_preview.set_paintable(texture)

    def create_menu_button(self, label, menu):
        button = Gtk.MenuButton()
        button.set_label(label)
        button.set_menu_model(menu)
        return button

    def button_clicked_draw(self, button):
        self.on_draw(None, None)

    def button_clicked_end_turn(self, button):
        self.on_end_turn(None, None)

    def set_tile_preview(self, tile_name):
        image_path = utils.tile_image_path(tile_name)

        # Resize to 100x100
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=image_path,
            width=100,
            height=100,
            preserve_aspect_ratio=True,
        )

        # GTK4 Picture can take a pixbuf directly
        self.tile_preview.set_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))
