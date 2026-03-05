"""This module implements the BoardView class for displaying the game board."""
import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gdk, GdkPixbuf
import os
import math
from typing import Any

import re
from carcassonne.Presentation.Interfaces.IGameService import IGameService

PLACEMENT_RE = re.compile(r"^(?P<target>\d+)(?P<side>[NESW])(?P<rot>[0-3])$")
MEEPLE_SET = {"N", "E", "S", "W"}

class BoardView(Gtk.DrawingArea):
    def __init__(self, game_service: IGameService, game_gui: Any, tile_size: int = 100) -> None:
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

        self.selected_zone = []

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
    
    def get_tile_image_path(self, name: str) -> str:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        images_dir = os.path.join(base_dir, "Images")
        if(name.find("/") != -1):
            name = name.split("/")
            return os.path.join(images_dir, f"{name[0]}{name[1]}.png")
        return os.path.join(images_dir, f"{name}.png")
            
    def load_textures(self) -> None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        images_dir = os.path.join(base_dir, "Images")
        images_dir = os.path.normpath(images_dir)

        if not os.path.exists(images_dir):
            print(f"Images folder not found: {images_dir}")
            return

        for file in os.listdir(images_dir):
            if file.endswith(".png"):

                # garde exactement le nom du fichier sans l'extension
                name = os.path.splitext(file)[0]  
                full_path = os.path.join(images_dir, file)

                print(f"Loading texture: {name} from {full_path}")

                self.textures[name] = GdkPixbuf.Pixbuf.new_from_file(full_path)

        print("Images directory:", images_dir)


    # =========================
    # 🎨 DRAW
    # =========================
    def on_draw(self, area: Gtk.DrawingArea, cr: Any, width: int, height: int) -> None:

        cr.set_source_rgb(0.6, 0.6, 0.6)
        cr.paint()

        tiles = self.game.get_board_data()
        if not tiles:
            return
        
        if self.game_gui.current_move:
            temp_tile = self.parse_move(self.game_gui.current_move, self.game_gui.current_move_x, self.game_gui.current_move_y)
            if temp_tile:
                tiles = tiles + [temp_tile]


        positions = [(t["x"], t["y"]) for t in tiles]

        min_x = min(x for x, y in positions)
        min_y = min(y for x, y in positions)
        max_x = max(x for x, y in positions)
        max_y = max(y for x, y in positions)

        tile = self.tile_size
        
        board_width = (max_x - min_x + 1) * tile
        board_height = (max_y - min_y + 1) * tile

        offset_x, offset_y, min_x, min_y = self.get_board_offsets()

        for tile_data in tiles:
            grid_x = tile_data["x"]
            grid_y = tile_data["y"]

            x = offset_x + (grid_x - min_x) * tile
            y = offset_y + (grid_y - min_y) * tile

            self.draw_tile(cr, x, y, tile, tile_data)
        # Draw ghost tile
        if self.is_dragging and self.game_gui.current_tile and self.ghost_x is not None:
            self.draw_ghost_tile(cr)

    def parse_move(self, move: str, x: int, y: int) -> dict:
        if move.count('/')==1:
            name, rest = move.split("/")
            orientation = int(rest[-1])
            middle = ""
        else:
            name, middle, rest = move.split("/")
            orientation = int(rest[-1])


        return {
            "id":self.game_gui.nb_tiles,
            "x": x,
            "y": y,
            "name": name,
            "middle": middle,
            "orientation": orientation
            
        }

    def draw_ghost_tile(self, cr: Any) -> None:
        name = self.game_gui.current_tile
        orientation = self.game_gui.current_orientation
        if name.find("/") != -1:
            name = name.split("/")
            name = f"{name[0]}{name[1]}"
        pixbuf = self.textures.get(name)
        if not pixbuf:
            return

        tile = self.tile_size

        # Convert mouse position to grid
        grid_x, grid_y = self.pixel_to_grid(self.ghost_x, self.ghost_y)

        # Convert back to pixel position (snap to grid)
        offset_x, offset_y, min_x, min_y = self.get_board_offsets()

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
    def draw_tile(self, cr: Any, x: int, y: int, size: int, tile_data: dict) -> None:
        name = tile_data["name"]+tile_data["middle"] if tile_data["middle"] else tile_data["name"]
        orientation = tile_data["orientation"]
        print(f"Drawing tile {name} at ({x}, {y}) with orientation {orientation}")

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
        if self.game_gui.current_move_x==tile_data["x"] and self.game_gui.current_move_y==tile_data["y"] and self.game_gui.current_move!=None:
            cr.set_source_rgb(0, 1, 0)  # vert
            # ----- GRILLE 3x3 -----
            cr.set_source_rgb(0, 1, 0)
            cr.set_line_width(1)

            cell = size / 3

            # lignes verticales
            cr.move_to(x + cell, y)
            cr.line_to(x + cell, y + size)

            cr.move_to(x + 2*cell, y)
            cr.line_to(x + 2*cell, y + size)

            # lignes horizontales
            cr.move_to(x, y + cell)
            cr.line_to(x + size, y + cell)

            cr.move_to(x, y + 2*cell)
            cr.line_to(x + size, y + 2*cell)

        else:
            cr.set_source_rgb(0, 0, 0)  # noir
        
        meeples = self.game.get_meeples_data()
        print(meeples)

        for m in meeples:
            for m in meeples:
                if m["tile_id"] == tile_data["id"]:
                    position_map = {
                        7: (0,0), 0: (0,1), 1: (0,2),
                        6: (1,0), 8: (1,1), 2: (1,2),
                        5: (2,0), 4: (2,1), 3: (2,2)
                    }
                    row, col = position_map.get(m["position"], (1,1))  # centre par défaut

                    cell = size / 3
                    cx = x + col * cell
                    cy = y + row * cell
                    padding = cell * 0.2

                    cr.set_source_rgb(1, 0, 0)  # rouge
                    cr.set_line_width(3)

                    # diagonales de la croix
                    cr.move_to(cx + padding, cy + padding)
                    cr.line_to(cx + cell - padding, cy + cell - padding)

                    cr.move_to(cx + cell - padding, cy + padding)
                    cr.line_to(cx + padding, cy + cell - padding)

                    cr.stroke()

        cr.set_line_width(2)
        cr.rectangle(x, y, size, size)
        cr.stroke()

    # =========================
    # 🖱️ CLICK
    # =========================
    def on_click(self, gesture: Any, n_press: int, mouse_x: int, mouse_y: int) -> None:
        
        grid_x, grid_y = self.pixel_to_grid(mouse_x, mouse_y)

        print(f"Clicked grid position: {grid_x}, {grid_y}")

        if self.game_gui.current_tile:
            vertex_id, side = self.game.get_close_neighbors(grid_x, grid_y)

            if vertex_id is not None and side is not None:
                orientation = self.game_gui.current_orientation
                move_str = f"{self.game_gui.current_tile}/{vertex_id}{['N','E','S','W'][side]}{orientation}"
                print(f"Attempting to play move: {move_str}")
                
                self.game_gui.current_move = move_str
                self.game_gui.current_move_x = grid_x
                self.game_gui.current_move_y = grid_y
                self.game_gui.nb_tiles=self.game_gui.nb_tiles+1
                
                print(self.game_gui.current_move)

                self.game_gui.current_tile = None
                self.is_dragging = False
                self.ghost_x = None
                self.ghost_y = None

                self.queue_draw()
                return
        
        if self.game_gui.current_move:
            offset_x, offset_y, min_x, min_y = self.get_board_offsets()
            tile = self.tile_size

            lx = self.game_gui.current_move_x
            ly = self.game_gui.current_move_y

            tile_px = offset_x + (lx - min_x) * tile
            tile_py = offset_y + (ly - min_y) * tile

            if tile_px <= mouse_x <= tile_px + tile and \
            tile_py <= mouse_y <= tile_py + tile:

                cell = tile / 3

                col = int((mouse_x - tile_px) // cell)
                row = int((mouse_y - tile_py) // cell)

                positions = [
                    ["NW", "N", "NE"],
                    ["W",  "C", "E"],
                    ["SW", "S", "SE"]
                ]

                result = positions[row][col]
                print("Zone cliquée :", result)
                self.game_gui.current_move = self.game_gui.current_move + "/"+result

                return

    
        self.queue_draw()

    def on_drop(self, controller: Any, value: str, x: int, y: int) -> bool:
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
            self.game_gui.current_move=move_str
            #self.game.play_move(move_str)

        self.queue_draw()
        return True

    def on_key_press(self, controller: Any, keyval: int, keycode: int, state: Any) -> bool:
        step = 20  # pixels de déplacement
        if keyval == Gdk.KEY_z:      # haut
            self.offset_y += step
        elif keyval == Gdk.KEY_s:    # bas
            self.offset_y -= step
        elif keyval == Gdk.KEY_q:    # gauche
            self.offset_x += step
        elif keyval == Gdk.KEY_d:    # droite
            self.offset_x -= step
        elif keyval == Gdk.KEY_r:
            self.game_gui.rotate_current_tile()

        self.queue_draw()
        return True  # signal consommé
    
    def get_board_offsets(self) -> tuple[int, int, int, int]:
        tiles = self.game.get_board_data()
        if not tiles:
            return 0, 0, 0, 0

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

        base_offset_x = (width - board_width) // 2
        base_offset_y = (height - board_height) // 2

        # 👇 OFFSET GLOBAL (centrage + déplacement utilisateur)
        final_offset_x = base_offset_x + self.offset_x
        final_offset_y = base_offset_y + self.offset_y

        return final_offset_x, final_offset_y, min_x, min_y

    def pixel_to_grid(self, mouse_x: int, mouse_y: int) -> tuple[int, int]:
        tiles = self.game.get_board_data()
        if not tiles:
            return 0, 0

        offset_x, offset_y, min_x, min_y = self.get_board_offsets()

        tile = self.tile_size

        grid_x = int((mouse_x - offset_x) // tile) + min_x
        grid_y = int((mouse_y - offset_y) // tile) + min_y

        return grid_x, grid_y

    # =========================
    # 🔄 REFRESH
    # =========================
    def refresh(self) -> None:
        self.queue_draw()


    def on_mouse_move(self, controller: Any, x: int, y: int) -> None:
        if self.is_dragging and self.game_gui.current_tile:
            self.ghost_x = x
            self.ghost_y = y
            self.queue_draw()

    def on_mouse_release(self, gesture: Any, n_press: int, mouse_x: int, mouse_y: int) -> None:
        if not self.is_dragging or not self.game_gui.current_tile:
            return

        grid_x, grid_y = self.pixel_to_grid(mouse_x, mouse_y)

        vertex_id, side = self.game.get_close_neighbors(grid_x, grid_y)

        if vertex_id is not None and side is not None:
            orientation = self.game_gui.current_orientation
            move_str = f"{self.game_gui.current_tile}/{vertex_id}{['N','E','S','W'][side]}{orientation}"
            self.game_gui.current_move=move_str
            #self.game.play_move(move_str)

            # Clear tile only if placement succeeded
            self.game_gui.current_tile = None

        # Stop ghost
        self.is_dragging = False
        self.ghost_x = None
        self.ghost_y = None

        self.queue_draw()