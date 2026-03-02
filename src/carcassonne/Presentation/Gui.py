import os

from carcassonne.Presentation import CommandsHandlerGui
from carcassonne.Presentation.BoardView import BoardView
from carcassonne.Presentation.GameConfiguration import GameConfiguration
from carcassonne.Presentation.Interfaces.IGameService import IGameService
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GLib, Gtk, Gio, Gdk, GdkPixbuf


class GameGUI(Gtk.Application):
    
    def __init__(self, game_service: IGameService):
        super().__init__(application_id="com.example.Carcassonne", flags=0)
        GLib.set_application_name('Carcassonne')
        
        self.game = game_service
        self.settings = GameConfiguration().settings
        self.running = True
        self.current_tile = None
        self.current_orientation = 0  # 0,1,2,3 → 0°, 90°, 180°, 270°

        self.load_css()

        self.button_draw = Gtk.Button(label="Draw Tile (t)")
        self.button_draw.connect("clicked", self.button_clicked_draw)
        

    def reset(self):
        self.current_tile = None
        self.current_orientation = 0
        self.tile_preview.set_filename("")  # Clear preview
        self.board_view.refresh()

    def do_activate(self):
        window = Gtk.ApplicationWindow(application=self)
        window.set_title("Carcassonne")
        window.set_default_size(1080, 720)

        self.stack = Gtk.Stack()
        window.set_child(self.stack)

        # Crée les vues
        self.menu_view = self.create_main_menu()

        # Ajoute au stack
        self.stack.add_named(self.menu_view, "menu")

        


        header = Gtk.HeaderBar()
        window.set_titlebar(header)

        menu_file = Gio.Menu()
        menu_file.append("New Game", "app.new")
        self.set_accels_for_action("app.new", ["<Primary>n"])
        menu_file.append("Load Game", "app.load")
        self.set_accels_for_action("app.load", ["<Primary>l"])
        menu_file.append("Save Game", "app.save")
        self.set_accels_for_action("app.save", ["<Primary>s"])
        menu_file.append("Configuration", "app.config")
        self.set_accels_for_action("app.config", ["<Primary>comma"])
        menu_file.append("Info", "app.info")
        self.set_accels_for_action("app.info", ["<Primary>i"])
        menu_file.append("Quit", "app.quit")
        self.set_accels_for_action("app.quit", ["<Primary>q"])

        menu_game = Gio.Menu()
        menu_game.append("Undo", "app.undo")
        self.set_accels_for_action("app.undo", ["<Primary>u"])
        menu_game.append("Redo", "app.redo")
        self.set_accels_for_action("app.redo", ["<Primary>r"])
        menu_game.append("Pause", "app.pause")
        self.set_accels_for_action("app.pause", ["<Primary>p"])
        menu_game.append("Hint", "app.hint")
        self.set_accels_for_action("app.hint", ["<Primary>h"])

        menu_button = self.create_menu_button("File", menu_file)
        menu_button_game = self.create_menu_button("Game", menu_game)

        header.pack_start(menu_button)
        header.pack_start(menu_button_game)

        def new_game_action(action, parameter):
            CommandsHandlerGui.on_new(self.game)
            self.reset()

        self.create_action("new", new_game_action)
        self.create_action("load", lambda a, p: CommandsHandlerGui.on_load())
        self.create_action("save", lambda a, p: CommandsHandlerGui.on_save())
        self.create_action("config", lambda a, p: CommandsHandlerGui.on_config())
        self.create_action("info", lambda a, p: CommandsHandlerGui.on_info())
        self.create_action("quit", lambda a, p: CommandsHandlerGui.on_quit(self))
        self.create_action("undo", lambda a, p: CommandsHandlerGui.on_undo())
        self.create_action("redo", lambda a, p: CommandsHandlerGui.on_redo())
        self.create_action("pause", lambda a, p: CommandsHandlerGui.on_pause())
        self.create_action("hint", lambda a, p: CommandsHandlerGui.on_hint())

        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", lambda a, p: CommandsHandlerGui.on_quit(self))
        self.add_action(quit_action)


        overlay = Gtk.Overlay()

        
        self.board_view = BoardView(self.game, self)
        overlay.set_child(self.board_view)

        corner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        corner_box.set_margin_end(15)
        corner_box.set_margin_bottom(15)

        corner_box.set_halign(Gtk.Align.END)
        corner_box.set_valign(Gtk.Align.END)

        corner_box.add_css_class("corner-panel")
    
        self.tile_preview = Gtk.Picture()
        self.tile_preview.set_content_fit(Gtk.ContentFit.COVER)
        self.tile_preview.set_size_request(100, 100)
        self.tile_preview.set_hexpand(False)
        self.tile_preview.set_vexpand(False)

        click = Gtk.GestureClick()
        click.connect("pressed", self.on_preview_pressed)
        #click.connect("released", self.on_preview_released)
        self.tile_preview.add_controller(click)

        drag_source = Gtk.DragSource()
        """drag_source.set_actions(Gdk.DragAction.MOVE)

        drag_source.connect("prepare", self.on_drag_prepare)
        #drag_source.connect("drag-begin", self.on_drag_begin)
        drag_source.connect("drag-begin", lambda s, d: s.set_icon(None, 0, 0))"""
        

        corner_box.append(self.tile_preview)
        corner_box.append(self.button_draw)

        overlay.add_overlay(corner_box)

        self.create_action("draw", self.on_draw)
        self.set_accels_for_action("app.draw", ["t"])
        self.create_action("rotate", self.on_rotate)
        self.set_accels_for_action("app.rotate", ["r"])

        self.stack.add_named(overlay, "game")

        # Affiche le menu au démarrage
        self.stack.set_visible_child_name("menu")

        window.present()

    def on_rotate(self, action, param):
        self.rotate_current_tile()

    def on_preview_pressed(self, gesture, n_press, x, y):
        if not self.current_tile:
            return

        self.board_view.is_dragging = True

        # Start ghost at center of board
        width = self.board_view.get_allocated_width()
        height = self.board_view.get_allocated_height()

        self.board_view.ghost_x = width // 2
        self.board_view.ghost_y = height // 2

        self.board_view.grab_focus()
        self.board_view.queue_draw()

    def on_preview_released(self, gesture, n_press, x, y):
        self.board_view.is_dragging = False
        self.board_view.queue_draw()

    def create_main_menu(self):
        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=20,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER
        )

        title = Gtk.Label(label="Carcassonne")
        title.add_css_class("title-1")

        btn_single = Gtk.Button(label="Singleplayer")
        btn_multi = Gtk.Button(label="Multiplayer")
        btn_quit = Gtk.Button(label="Quit")

        btn_single.connect("clicked", self.start_singleplayer)
        btn_multi.connect("clicked", self.start_multiplayer)
        btn_quit.connect("clicked", lambda b: self.quit())

        box.append(title)
        box.append(btn_single)
        box.append(btn_multi)
        box.append(btn_quit)

        return box
    
    def start_singleplayer(self, button):
        #self.game.start_new_game(mode="single")
        self.stack.set_visible_child_name("game")
        self.board_view.grab_focus()

    def start_multiplayer(self, button):
        #self.game.start_new_game(mode="multi")
        self.stack.set_visible_child_name("game")


    

    def on_draw(self, action, param):
        tile = self.game.draw_tile()
        self.current_orientation = 0  # reset rotation
        
        self.current_tile = tile

        image_path = self.get_tile_image_path(tile)
        print(f"Drew tile: {tile} → image path: {image_path}")
        self.tile_preview.set_filename(image_path)
        self.board_view.refresh()
    
    def rotate_current_tile(self):
        if self.current_tile is None:
            return

        self.current_orientation = (self.current_orientation + 1) % 4
        print("Orientation:", self.current_orientation)

        # Rotate preview visually
        self.update_preview_rotation()

    def update_preview_rotation(self):
        if not self.current_tile:
            return

        image_path = self.get_tile_image_path(self.current_tile)

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
            GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE][self.current_orientation]
        )

        texture = Gdk.Texture.new_for_pixbuf(rotated)
        self.tile_preview.set_paintable(texture)

    def on_drag_prepare(self, source, x, y):
        if not self.current_tile:
            return None

        # Load the pixbuf of the current tile
    # Provide tile name for drop logic
        return Gdk.ContentProvider.new_for_value(self.current_tile)
    
    def on_drag_begin(self, drag_source, drag):

        if not self.current_tile:
            return

        image_path = self.get_tile_image_path(self.current_tile)

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

        rotated = pixbuf.rotate_simple(rotations[self.current_orientation])

        texture = Gdk.Texture.new_for_pixbuf(rotated)

        # Store reference to avoid GC
        self._drag_texture = texture

        # Center cursor on tile
        drag_source.set_icon(texture, 50, 50)

    def create_action(self, name, callback):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)

    def create_menu_button(self, label, menu):
        button = Gtk.MenuButton()
        button.set_label(label)
        button.set_menu_model(menu)
        return button
    
    def button_clicked_draw(self, button):
        self.on_draw(None, None)

    def get_tile_image_path(self, name):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        images_dir = os.path.join(base_dir, "Images")
        if(name.find("/") != -1):
            name = name.split("/")
            return os.path.join(images_dir, f"{name[0]}{name[1]}.png")
        return os.path.join(images_dir, f"{name}.png")

    def set_tile_preview(self, tile_name):
        image_path = self.get_tile_image_path(tile_name)
        
        # Resize to 100x100
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=image_path,
            width=100,
            height=100,
            preserve_aspect_ratio=True
        )

        # GTK4 Picture can take a pixbuf directly
        self.tile_preview.set_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))
    

    

    
    def load_css(self):
        css = """
        .corner-panel {
            background-color: rgba(0, 0, 0, 0.6);
            border: 3px solid white;
            border-radius: 12px;
            padding: 12px;
        }
        """

        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode())

        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )