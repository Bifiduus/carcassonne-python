import os

from carcassonne.Presentation.Gui import CommandsHandlerGui
from carcassonne.Presentation.Gui.BoardView import BoardView
from carcassonne.Presentation.Gui.WindowView import WindowView
from carcassonne.Presentation.Gui import utils
from carcassonne.Presentation.Gui.MainMenu import MainMenu
from carcassonne.Presentation.Gui.TilePreview import TilePreview

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk, Gio, Gdk, GdkPixbuf


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
            "clicked", lambda b: CommandsHandlerGui.on_draw_gui(self)
        )

        self.button_end_turn = Gtk.Button(label="End Turn (space)")
        self.button_end_turn.connect(
            "clicked", lambda b: CommandsHandlerGui.on_end_turn_gui(self)
        )

    def do_activate(self):
        window = WindowView(self, self.game_data)
        self.window = window

        # main menu is now produced by a small helper
        self.menu_view = MainMenu.create(self)
        window.stack.add_named(self.menu_view, "menu")

        # register actions used by the menus and shortcuts
        register = utils.register_action
        register(self, "new", lambda a, p: CommandsHandlerGui.on_new_gui(self))
        register(self, "load", lambda a, p: CommandsHandlerGui.on_load())
        register(self, "save", lambda a, p: CommandsHandlerGui.on_save())
        register(self, "config", lambda a, p: CommandsHandlerGui.on_config())
        register(self, "info", lambda a, p: CommandsHandlerGui.on_info())
        register(self, "quit", lambda a, p: CommandsHandlerGui.on_quit(self))
        register(self, "undo", lambda a, p: CommandsHandlerGui.on_undo_gui(self))
        register(self, "redo", lambda a, p: CommandsHandlerGui.on_redo_gui(self))
        register(self, "pause", lambda a, p: CommandsHandlerGui.on_pause())
        register(self, "hint", lambda a, p: CommandsHandlerGui.on_hint())

        # the ``WindowView`` helper already attaches the file/game menus; an
        # explicit quit action is duplicated here for safety.
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda a, p: CommandsHandlerGui.on_quit(self))
        self.add_action(quit_action)

        # ----------- game overlay (board + controls) -----------------------
        overlay = Gtk.Overlay()

        self.board_view = BoardView(self.game_data)
        self.game_data.set_board_view(self.board_view)
        overlay.set_child(self.board_view)

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
        register(self, "draw", lambda a, p: CommandsHandlerGui.on_draw_gui(self))
        self.set_accels_for_action("app.draw", ["t"])
        register(self, "rotate", lambda a, p: CommandsHandlerGui.on_rotate_gui(self))
        self.set_accels_for_action("app.rotate", ["r"])
        register(self, "end_turn", lambda a, p: CommandsHandlerGui.on_end_turn_gui(self))
        self.set_accels_for_action("app.end_turn", ["space"])

        window.stack.add_named(overlay, "game")
        window.stack.set_visible_child_name("menu")
        # make the window visible on screen
        window.window.present()

    def on_end_turn(self, action, param):
        # kept for backward compatibility; newer code should use CommandsHandlerGui
        CommandsHandlerGui.on_end_turn_gui(self)

    def on_rotate(self, action, param):
        CommandsHandlerGui.on_rotate_gui(self)

    def on_preview_pressed(self, gesture, n_press, x, y):
        if not self.game_data.current_tile:
            return

        self.game_data.is_dragging = True

        # Start ghost at center of board
        width = self.board_view.get_allocated_width()
        height = self.board_view.get_allocated_height()

        self.board_view.ghost_x = width // 2
        self.board_view.ghost_y = height // 2

        self.board_view.grab_focus()
        self.board_view.queue_draw()
        

    def on_preview_released(self, gesture, n_press, x, y):
        self.game_data.is_dragging = False
        self.game_data.refresh()
    
    def start_singleplayer(self, button):
        #self.game.start_new_game(mode="single")
        self.window.stack.set_visible_child_name("game")
        self.board_view.grab_focus()

    def start_multiplayer(self, button):
        #self.game.start_new_game(mode="multi")
        self.window.stack.set_visible_child_name("game")


    

    def on_draw(self, action, param):
        # legacy entry point; forward to handler
        CommandsHandlerGui.on_draw_gui(self)
    
    
    def update_preview_rotation(self):
        if not self.game_data.current_tile:
            return

        image_path = utils.tile_image_path(self.game_data.current_tile.current_tile)

        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=image_path,
            width=100,
            height=100,
            preserve_aspect_ratio=True
        )

        # Rotate pixbuf
        rotated = pixbuf.rotate_simple(
            [GdkPixbuf.PixbufRotation.NONE,
            GdkPixbuf.PixbufRotation.CLOCKWISE,
            GdkPixbuf.PixbufRotation.UPSIDEDOWN,
            GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE][self.game_data.current_orientation]
        )

        texture = Gdk.Texture.new_for_pixbuf(rotated)
        self.tile_preview.set_paintable(texture)

    def on_drag_prepare(self, source, x, y):
        if not self.current_tile:
            return None

        # Load the pixbuf of the current tile
    # Provide tile name for drop logic
        return Gdk.ContentProvider.new_for_value(self.game_data.current_tile.current_tile)
    
    def on_drag_begin(self, drag_source, drag):

        if not self.current_tile:
            return

        image_path = utils.tile_image_path(self.game_data.current_tile.current_tile)

        # Load scaled image
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=image_path,
            width=100,
            height=100,
            preserve_aspect_ratio=True
        )

        rotations = [
            GdkPixbuf.PixbufRotation.NONE,
            GdkPixbuf.PixbufRotation.CLOCKWISE,
            GdkPixbuf.PixbufRotation.UPSIDEDOWN,
            GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE
        ]

        rotated = pixbuf.rotate_simple(rotations[self.game_data.current_orientation])

        texture = Gdk.Texture.new_for_pixbuf(rotated)

        # Store reference to avoid GC
        self._drag_texture = texture

        # Center cursor on tile
        drag_source.set_icon(texture, 50, 50)

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
            preserve_aspect_ratio=True
        )

        # GTK4 Picture can take a pixbuf directly
        self.tile_preview.set_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))
    