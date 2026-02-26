import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gdk, GdkPixbuf
import os
import math


class BoardView(Gtk.DrawingArea):
    def __init__(self, game_service, game_gui, tile_size=100):
        super().__init__()

        self.game = game_service
        self.game_gui = game_gui
        self.tile_size = tile_size

        self.set_content_width(900)
        self.set_content_height(700)
        self.set_draw_func(self.on_draw)

    
        self.textures = {}
        self.load_textures()

        self.offset_x = 0
        self.offset_y = 0

        self.ghost_x = None
        self.ghost_y = None

        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self.on_mouse_move)
        self.add_controller(motion)
       # self.tile_preview.add_controller(self.drag_source)
        self.is_dragging = False

        # permettre à la zone de recevoir le focus pour les touches
        self.set_focusable(True)
        self.grab_focus()

        """drop_target = Gtk.DropTarget.new(str, Gdk.DragAction.MOVE)
        drop_target.connect("drop", self.on_drop)
         self.add_controller(drop_target)"""

        click = Gtk.GestureClick()
        click.set_button(1)
        click.connect("released", self.on_mouse_release)
        click.connect("pressed", self.on_click)
        self.add_controller(click)

       

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_press)
        self.add_controller(key_controller)
            
    def load_textures(self):
            # chemin absolu vers le dossier Images
            base_dir = os.path.dirname(os.path.abspath(__file__))  # dossier actuel
            images_dir = os.path.join(base_dir, "Images")  # remonte jusqu'à la racine

            images_dir = os.path.normpath(images_dir)

            if not os.path.exists(images_dir):
                print(f"Images folder not found: {images_dir}")
                return

            for file in os.listdir(images_dir):
                if file.endswith(".png"):
                    name = file[:-4]  # enlever .png
                    path = os.path.join(images_dir, file)
                    self.textures[name] = GdkPixbuf.Pixbuf.new_from_file(path)
            print(images_dir)
            print(base_dir)

    # =========================
    # 🎨 DRAW
    # =========================
    def on_draw(self, area, cr, width, height):

        cr.set_source_rgb(0.6, 0.6, 0.6)
        cr.paint()

        tiles = self.game.get_board_data()
        if not tiles:
            return

        positions = [(t["x"], t["y"]) for t in tiles]

        min_x = min(x for x, y in positions)
        min_y = min(y for x, y in positions)
        max_x = max(x for x, y in positions)
        max_y = max(y for x, y in positions)

        tile = self.tile_size

        
        board_width = (max_x - min_x + 1) * tile
        board_height = (max_y - min_y + 1) * tile

        offset_x = (width - board_width) // 2
        offset_y = (height - board_height) // 2

        for tile_data in tiles:
            grid_x = tile_data["x"]
            grid_y = tile_data["y"]

            x = offset_x + (grid_x - min_x) * tile + self.offset_x
            y = offset_y + (grid_y - min_y) * tile + self.offset_y

            self.draw_tile(cr, x, y, tile, tile_data)
        # Draw ghost tile
        if self.is_dragging and self.game_gui.current_tile and self.ghost_x is not None:
            self.draw_ghost_tile(cr)

    def draw_ghost_tile(self, cr):
        name = self.game_gui.current_tile
        orientation = self.game_gui.current_orientation

        pixbuf = self.textures.get(name)
        if not pixbuf:
            return

        tile = self.tile_size

        # Convert mouse position to grid
        grid_x, grid_y = self.pixel_to_grid(self.ghost_x, self.ghost_y)

        # Convert back to pixel position (snap to grid)
        tiles = self.game.get_board_data()
        if not tiles:
            return

        positions = [(t["x"], t["y"]) for t in tiles]
        min_x = min(x for x, y in positions)
        min_y = min(y for x, y in positions)

        width = self.get_allocated_width()
        height = self.get_allocated_height()

        board_width = (max(x for x, _ in positions) - min_x + 1) * tile
        board_height = (max(y for _, y in positions) - min_y + 1) * tile

        offset_x = (width - board_width) // 2 + self.offset_x
        offset_y = (height - board_height) // 2 + self.offset_y

        x = offset_x + (grid_x - min_x) * tile
        y = offset_y + (grid_y - min_y) * tile

        cr.save()

        # Make semi transparent
        #cr.set_source_rgba(1, 1, 1, 0.6)

        angle = orientation * 90

        cr.translate(x + tile / 2, y + tile / 2)
        cr.rotate(math.radians(angle))

        scale_x = tile / pixbuf.get_width()
        scale_y = tile / pixbuf.get_height()
        cr.scale(scale_x, scale_y)

        Gdk.cairo_set_source_pixbuf(
            cr,
            pixbuf,
            -pixbuf.get_width() / 2,
            -pixbuf.get_height() / 2
        )

        cr.paint_with_alpha(0.6)

        cr.restore()


    # =========================
    # 🧩 DRAW ONE TILE
    # =========================
    def draw_tile(self, cr, x, y, size, tile_data):
        name = tile_data["name"]
        orientation = tile_data["orientation"]
        #print(f"Drawing tile {name} at ({x}, {y}) with orientation {orientation}")

        pixbuf = self.textures.get(name)

        if not pixbuf:
            cr.set_source_rgb(1, 1, 1)
            cr.rectangle(x, y, size, size)
            cr.fill()
        else:
            cr.save()

            angle = orientation * 90

            cr.translate(x + size / 2, y + size / 2)
            cr.rotate(math.radians(angle))

            scale_x = size / pixbuf.get_width()
            scale_y = size / pixbuf.get_height()
            cr.scale(scale_x, scale_y)

            Gdk.cairo_set_source_pixbuf(
                cr,
                pixbuf,
                -pixbuf.get_width() / 2,
                -pixbuf.get_height() / 2
            )

            cr.paint()
            cr.restore()

        # Bordure
        cr.set_source_rgb(0, 0, 0)
        cr.rectangle(x, y, size, size)
        cr.stroke()

    # =========================
    # 🖱️ CLICK
    # =========================
    def on_click(self, gesture, n_press, mouse_x, mouse_y):
        
        tiles = self.game.get_board_data()
        if not tiles:
            return

        positions = [(t["x"], t["y"]) for t in tiles]

        min_x = min(x for x, y in positions)
        min_y = min(y for x, y in positions)
        max_x = max(x for x, y in positions)
        max_y = max(y for x, y in positions)

        tile = self.tile_size

        width = self.get_allocated_width()
        height = self.get_allocated_height()

        board_width = (max_x - min_x + 1) * tile
        board_height = (max_y - min_y + 1) * tile

        offset_x = (width - board_width) // 2
        offset_y = (height - board_height) // 2

        grid_x = int((mouse_x - offset_x) // tile) + min_x
        grid_y = int((mouse_y - offset_y) // tile) + min_y 

        print(f"Clicked grid position: {grid_x}, {grid_y}")

        if self.game_gui.current_tile:
            vertex_id, side = self.game.get_close_neighbors(grid_x, grid_y)

            if vertex_id is not None and side is not None:
                orientation = self.game_gui.current_orientation
                move_str = f"{self.game_gui.current_tile}/{vertex_id}{['N','E','S','W'][side]}{orientation}"
                self.game.play_move(move_str)

                self.game_gui.current_tile = None
                self.is_dragging = False
                self.ghost_x = None
                self.ghost_y = None

                self.queue_draw()
                return

    
        self.queue_draw()

    def on_drop(self, controller, value, x, y):
        tile_name = value  # string reçue

        print("Dropped tile:", tile_name)

        # Convertir coordonnées pixels → grille
        grid_x, grid_y = self.pixel_to_grid(x, y)

        print("Grid position:", grid_x, grid_y)

        # Appeler le game service
        vertex_id, side = self.game.get_close_neighbors(grid_x, grid_y)
        if vertex_id is not None and side is not None:
            orientation = self.game_gui.current_orientation
            move_str = f"{tile_name}/{vertex_id}{['N','E','S','W'][side]}{orientation}"
            self.game.play_move(move_str)

        self.queue_draw()
        return True

    def on_key_press(self, controller, keyval, keycode, state):
        step = 20  # pixels de déplacement
        if keyval == Gdk.KEY_z:      # haut
            self.offset_y -= step
        elif keyval == Gdk.KEY_s:    # bas
            self.offset_y += step
        elif keyval == Gdk.KEY_q:    # gauche
            self.offset_x -= step
        elif keyval == Gdk.KEY_d:    # droite
            self.offset_x += step
        elif keyval == Gdk.KEY_r:
            self.game_gui.rotate_current_tile()

        self.queue_draw()
        return True  # signal consommé

    def pixel_to_grid(self, mouse_x, mouse_y):
        mouse_x += -self.offset_x
        mouse_y += -self.offset_y
        tiles = self.game.get_board_data()
        if not tiles:
            return 0, 0

        positions = [(t["x"], t["y"]) for t in tiles]

        min_x = min(x for x, y in positions)
        min_y = min(y for x, y in positions)

        width = self.get_allocated_width()
        height = self.get_allocated_height()

        tile = self.tile_size

        board_width = (max(x for x, _ in positions) - min_x + 1) * tile
        board_height = (max(y for _, y in positions) - min_y + 1) * tile

        offset_x = (width - board_width) // 2
        offset_y = (height - board_height) // 2

        grid_x = int((mouse_x - offset_x) // tile) + min_x
        grid_y = int((mouse_y - offset_y) // tile) + min_y

        return grid_x, grid_y

    # =========================
    # 🔄 REFRESH
    # =========================
    def refresh(self):
        self.queue_draw()


    def on_mouse_move(self, controller, x, y):
        if self.is_dragging and self.game_gui.current_tile:
            self.ghost_x = x
            self.ghost_y = y
            self.queue_draw()

    def on_mouse_release(self, gesture, n_press, mouse_x, mouse_y):
        if not self.is_dragging or not self.game_gui.current_tile:
            return

        grid_x, grid_y = self.pixel_to_grid(mouse_x, mouse_y)

        vertex_id, side = self.game.get_close_neighbors(grid_x, grid_y)

        if vertex_id is not None and side is not None:
            orientation = self.game_gui.current_orientation
            move_str = f"{self.game_gui.current_tile}/{vertex_id}{['N','E','S','W'][side]}{orientation}"
            self.game.play_move(move_str)

            # Clear tile only if placement succeeded
            self.game_gui.current_tile = None

        # Stop ghost
        self.is_dragging = False
        self.ghost_x = None
        self.ghost_y = None

        self.queue_draw()