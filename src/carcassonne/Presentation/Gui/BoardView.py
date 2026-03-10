import gi
gi.require_version("Gtk", "4.0")

from gi.repository import Gtk, Gdk, GdkPixbuf
import os
from typing import Dict, Any, Tuple

from carcassonne.Presentation.Gui import board_utils

class BoardView(Gtk.DrawingArea):
    def __init__(self, game_data, tile_size=100):
        super().__init__()

        self.game_data = game_data
        self.tile_size = tile_size
        # content dimensions are arbitrary; the drawing code will adapt
        self.set_content_width(900)
        self.set_content_height(700)
        self.set_draw_func(self.on_draw)

        self.textures: Dict[str, GdkPixbuf.Pixbuf] = {}
        self.load_textures()

        self.offset_x = 0
        self.offset_y = 0
        self.ghost_x = None
        self.ghost_y = None

        self._setup_input_controllers()
        # flag used by the drag/ghost logic; set by GameGUI when the
        # preview is pressed
        self.game_data.is_dragging = False

        # ensure keyboard events can be received
        self.set_focusable(True)
        self.grab_focus()

    # ---------- internal helpers ----------------------------------------
    def _setup_input_controllers(self) -> None:
        """Create and attach the various GTK event controllers used by the
        board (mouse motion, clicks, key presses).
        """
        motion = Gtk.EventControllerMotion()
        motion.connect("motion", self.on_mouse_move)
        self.add_controller(motion)

        click = Gtk.GestureClick()
        click.set_button(1)
        click.connect("released", self.on_mouse_release)
        click.connect("pressed", self.on_click)
        self.add_controller(click)

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_press)
        self.add_controller(key_controller)

        # accept drops from the preview widget (tile name strings)
        drop = Gtk.DropTarget.new(str, Gdk.DragAction.COPY)
        drop.connect("drop", self.on_drop)
        self.add_controller(drop)

    def _normalize_name(self, name: str) -> str:
        """Turn a tile identifier into the key used in ``self.textures``.

        A name like "XX/NN" becomes "XXNN"; others are left unchanged.
        """
        if "/" in name:
            parts = name.split("/")
            return f"{parts[0]}{parts[1]}"
        return name

    def load_textures(self) -> None:
        """Populate ``self.textures`` with all PNG images found in the
        shared ``Images`` directory.
        """
        from carcassonne.Presentation.Gui.utils import get_images_dir

        images_dir = get_images_dir()

        if not os.path.isdir(images_dir):
            # silently ignore missing folder; GUI will draw empty tiles.
            return

        for file in os.listdir(images_dir):
            if file.lower().endswith(".png"):
                name = os.path.splitext(file)[0]
                full_path = os.path.join(images_dir, file)
                self.textures[name] = GdkPixbuf.Pixbuf.new_from_file(full_path)


    # =========================
    # 🎨 DRAW
    # =========================
    def on_draw(self, area, cr, width, height):
        """Main draw callback passed to ``set_draw_func``.

        Paints the board background, all placed tiles, optionally the tile
        currently being dragged, and any meeples.
        """
        cr.set_source_rgb(0.6, 0.6, 0.6)
        cr.paint()

        tiles = self.game_data.game.get_board_data()
        if not tiles:
            return

        # if there is a pending placement, append it to the list so the
        # preview shows on the board
        if self.game_data.current_tile and self.game_data.current_tile.move:
            temp = self.game_data.current_tile.parse_move(
                self.game_data.current_tile.move,
                self.game_data.current_tile.x,
                self.game_data.current_tile.y,
            )
            if temp:
                tiles = tiles + [temp]

        offset_x, offset_y, min_x, min_y = self.get_board_offsets()
        size = self.tile_size

        for t in tiles:
            x = offset_x + (t["x"] - min_x) * size
            y = offset_y + (t["y"] - min_y) * size
            self.draw_tile(cr, x, y, size, t)

        if self.game_data.is_dragging and self.ghost_x is not None:
            self.draw_ghost_tile(cr)

    

    def draw_ghost_tile(self, cr):
        """Draw a semi‑transparent copy of the tile that is currently being
        dragged.  The tile is snapped to the grid before rendering.
        """
        if not (self.game_data.current_tile and self.game_data.current_tile.current_tile):
            return

        name = board_utils.normalize_name(self.game_data.current_tile.current_tile)
        pixbuf = self.textures.get(name)
        if not pixbuf:
            return

        tile = self.tile_size
        # `self.ghost_x`/`ghost_y` are guarded by the caller, assert for type
        assert self.ghost_x is not None and self.ghost_y is not None
        grid_x, grid_y = self.pixel_to_grid(self.ghost_x, self.ghost_y)
        offset_x, offset_y, min_x, min_y = self.get_board_offsets()
        x = offset_x + (grid_x - min_x) * tile
        y = offset_y + (grid_y - min_y) * tile

        # the heavy lifting is handled by the helper; 0.6 alpha for ghost
        board_utils.draw_pixbuf_with_alpha(
            cr, x, y, tile, pixbuf, self.game_data.current_orientation, 0.6
        )


    # =========================
    # 🧩 DRAW ONE TILE
    # =========================
    def draw_tile(self, cr, x: float, y: float, size: float, tile_data: Dict[str, Any]) -> None:
        """Draw a single placed tile at pixel coordinates ``x,y``.

        ``tile_data`` is expected to be the dictionary returned by
        ``TilesView.parse_move`` or from ``game.get_board_data()``.
        """
        name = board_utils.normalize_name(tile_data["name"] + tile_data["middle"] if tile_data["middle"] else tile_data["name"])
        orientation = tile_data["orientation"]

        pixbuf = self.textures.get(name)
        if pixbuf:
            board_utils.draw_pixbuf(cr, x, y, size, pixbuf, orientation)
        else:
            cr.set_source_rgb(1, 1, 1)
            cr.rectangle(x, y, size, size)
            cr.fill()

        if board_utils.is_previewed_tile(self.game_data.current_tile, tile_data):
            board_utils.draw_preview_grid(cr, x, y, size)
        else:
            cr.set_source_rgb(0, 0, 0)

        board_utils.draw_meeples(cr, x, y, size, self.game_data.game.get_meeples_data(), tile_data["id"])
        cr.set_line_width(2)
        cr.rectangle(x, y, size, size)
        cr.stroke()


    # =========================
    # 🖱️ CLICK
    # =========================
    def on_click(self, gesture, n_press, mouse_x, mouse_y):
        """Handle left‑button clicks on the board.

        There are two distinct interactions:

        1. **Placement click** – the first click when a tile is held will
           record the destination but *not* select a meeple.  If the tile
           arrived via a drag operation, we ignore this event entirely and
           let ``on_mouse_release`` or ``on_drop`` do the work.
        2. **Meeple click** – any subsequent click inside the already‑placed
           tile simply chooses a meeple position without altering the move.
        """
        # ignore clicks while we're already dragging; placement happens on
        # release instead
        if self.game_data.is_dragging:
            return

        if not self.game_data.current_tile:
            self.queue_draw()
            return

        # if the tile already has a move string, treat this as a
        # meeple‑selection click
        if self.game_data.current_tile.move:
            if self._click_within_current_tile(mouse_x, mouse_y):
                result = self._meeple_zone(mouse_x, mouse_y)
                self.game_data.current_tile.meeple_pos = result
                self.queue_draw()
            return

        # otherwise this is the first placement click
        grid_x, grid_y = self.pixel_to_grid(mouse_x, mouse_y)
        vertex_id, side = self.game_data.game.get_close_neighbors(grid_x, grid_y)
        if vertex_id is None or side is None:
            self.queue_draw()
            return

        orientation = self.game_data.current_orientation
        move_str = (
            f"{self.game_data.current_tile.current_tile}/"
            f"{vertex_id}{['N','E','S','W'][side]}{orientation}"
        )
        self.game_data.current_tile.move = move_str
        self.game_data.current_tile.x = grid_x
        self.game_data.current_tile.y = grid_y
        # stop any ghost; tile has been dropped by click
        self.game_data.is_dragging = False
        self.ghost_x = None
        self.ghost_y = None
        self.queue_draw()

    def _click_within_current_tile(self, mouse_x, mouse_y) -> bool:
        offsets = self.get_board_offsets()
        return board_utils.click_within_current_tile(mouse_x, mouse_y, offsets, self.tile_size, self.game_data.current_tile)

    def _meeple_zone(self, mouse_x, mouse_y) -> str:
        offsets = self.get_board_offsets()
        return board_utils.meeple_zone(mouse_x, mouse_y, offsets, self.tile_size, self.game_data.current_tile)

    def on_drop(self, controller, value, x, y):
        """Handle a tile name string dropped on the board.

        The preview widget already implements a Gtk.DragSource, so this
        method is the corresponding destination handler.  We translate the
        pointer coordinates to a grid location exactly as the click/release
        handlers do, storing the move string and tile coordinates.  Meeple
        placement remains a separate click after the drop.
        """
        tile_name = value
        grid_x, grid_y = self.pixel_to_grid(x, y)
        vertex_id, side = self.game_data.game.get_close_neighbors(grid_x, grid_y)
        if vertex_id is not None and side is not None and self.game_data.current_tile:
            orientation = self.game_data.current_orientation
            move_str = (
                f"{tile_name}/{vertex_id}{['N','E','S','W'][side]}{orientation}"
            )
            self.game_data.current_tile.move = move_str
            # remember where the tile will land so that a subsequent click
            # inside the square can choose a meeple position.
            self.game_data.current_tile.x = grid_x
            self.game_data.current_tile.y = grid_y
        self.queue_draw()
        return True

    def on_key_press(self, controller, keyval, keycode, state):
        step = 20
        if keyval == Gdk.KEY_z:      # up
            self.offset_y += step
        elif keyval == Gdk.KEY_s:    # down
            self.offset_y -= step
        elif keyval == Gdk.KEY_q:    # left
            self.offset_x += step
        elif keyval == Gdk.KEY_d:    # right
            self.offset_x -= step
        elif keyval == Gdk.KEY_r:
            self.game_data.rotate_current_tile()
        self.queue_draw()
        return True
    
    def get_board_offsets(self) -> Tuple[int, int, int, int]:
        tiles = self.game_data.game.get_board_data()
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
        return base_offset_x + self.offset_x, base_offset_y + self.offset_y, min_x, min_y

    def pixel_to_grid(self, mouse_x: float, mouse_y: float) -> Tuple[int, int]:
        """Convert pixel coordinates to grid coordinates."""
        tiles = self.game_data.game.get_board_data()
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
        """Convenience wrapper used by GameDataGui when state changes."""
        self.queue_draw()


    def on_mouse_move(self, controller, x, y):
        if self.game_data.is_dragging and self.game_data.current_tile:
            self.ghost_x, self.ghost_y = x, y
            self.queue_draw()

    def on_mouse_release(self, gesture, n_press, mouse_x, mouse_y):
        if not self.game_data.is_dragging or not self.game_data.current_tile:
            return

        grid_x, grid_y = self.pixel_to_grid(mouse_x, mouse_y)

        vertex_id, side = self.game_data.game.get_close_neighbors(grid_x, grid_y)

        if vertex_id is not None and side is not None:
            orientation = self.game_data.current_orientation
            move_str = (
                f"{self.game_data.current_tile.current_tile}/{vertex_id}"
                f"{['N','E','S','W'][side]}{orientation}"
            )
            self.game_data.current_tile.move = move_str
            self.game_data.current_tile.x = grid_x
            self.game_data.current_tile.y = grid_y
            # keep the tile in place so the player can pick a meeple later

        # Stop ghost regardless of whether the drop was valid
        self.game_data.is_dragging = False
        self.ghost_x = None
        self.ghost_y = None

        self.queue_draw()