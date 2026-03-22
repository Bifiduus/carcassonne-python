"""This module implements the BoardView class for displaying the game board."""

from carcassonne.presentation.gui import board_utils
from typing import Dict, Any, Tuple
import os
from gi.repository import Gtk, Gdk, GdkPixbuf
import gi

gi.require_version("Gtk", "4.0")


class BoardView(Gtk.DrawingArea):
    def __init__(self, game_data: Any, tile_size: int = 100) -> None:
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

        self.background: GdkPixbuf.Pixbuf | None = None

    def set_background(self, image_path: str) -> None:
        """Load a background image for the board."""
        if os.path.exists(image_path):
            self.background = GdkPixbuf.Pixbuf.new_from_file(image_path)
        else:
            self.background = None
        print(image_path)
        self.queue_draw()

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
        """drop = Gtk.DropTarget.new(str, Gdk.DragAction.MOVE)
        drop.connect("drop", self.on_drop)
        drop.connect("enter", self.on_drag_enter)
        drop.connect("motion", self.on_drag_motion)
        drop.connect("leave", self.on_drag_leave)
        self.add_controller(drop)"""

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
        from carcassonne.presentation.gui.utils import get_images_dir

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

    def on_draw(
        self, area: Gtk.DrawingArea, cr: Any, width: int, height: int
    ) -> None:
        """Main draw callback passed to ``set_draw_func``.

        Paints the board background, all placed tiles, optionally the tile
        currently being dragged, and any meeples.
        """

        # draw background image if available
        if self.background:
            scaled = self.background.scale_simple(
                width, height, GdkPixbuf.InterpType.BILINEAR
            )

            Gdk.cairo_set_source_pixbuf(cr, scaled, 0, 0)
            cr.paint()
        else:
            cr.set_source_rgb(0.6, 0.6, 0.6)
            cr.paint()
        """cr.set_source_rgb(0.6, 0.6, 0.6)
        cr.paint()"""

        board_data = self.game_data.game.get_board_data()
        if not board_data:
            return

        # if there is a pending placement, append it to the list so the
        # preview shows on the board
        tiles = board_data
        if self.game_data.current_tile and self.game_data.current_tile.move:
            temp = self.game_data.current_tile.parse_move(
                self.game_data.current_tile.move,
                self.game_data.current_tile.x,
                self.game_data.current_tile.y,
            )
            if temp:
                tiles = tiles + [temp]

        # if there is a hint tile, append it for transparent display
        if self.game_data.hint_tile:
            tiles = tiles + [self.game_data.hint_tile]

        offset_x, offset_y, min_x, min_y = self.get_board_offsets()
        size = self.tile_size

        # compute last tile index for each player
        player_last_i = {}
        for i in range(1, len(board_data)):  # start from 1
            turn = i - 1  # turn 0 for i=1
            player_id = self.game_data.game.players_order[turn % len(
                self.game_data.game.players_order)]
            player_last_i[player_id] = i

        for i, t in enumerate(tiles):
            x = offset_x + (t["x"] - min_x) * size
            y = offset_y + (t["y"] - min_y) * size
            border_color = None
            if i < len(board_data) and i > 0:
                turn = i - 1
                player_id = self.game_data.game.players_order[turn % len(
                    self.game_data.game.players_order)]
                if i == player_last_i.get(player_id):
                    player = self.game_data.game.players[player_id]
                    color_str = player.get_color()
                    border_color = board_utils.color_map.get(
                        color_str, (1, 0, 0))
            self.draw_tile(cr, x, y, size, t, border_color)

        if self.game_data.is_dragging and self.ghost_x is not None:
            self.draw_ghost_tile(cr)

    def draw_ghost_tile(self, cr):
        """Draw a semi‑transparent copy of the tile that is currently being
        dragged.  The tile is snapped to the grid before rendering.
        """
        if not (
            self.game_data.current_tile
            and self.game_data.current_tile.current_tile
        ):
            return

        name = board_utils.normalize_name(
            self.game_data.current_tile.current_tile
        )
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

    def draw_tile(self, cr, x, y, size, tile_data, border_color) -> None:
        """Draw a single placed tile at pixel coordinates ``x,y``.

        ``tile_data`` is expected to be the dictionary returned by
        ``TilesView.parse_move`` or from ``game.get_board_data()``.
        """
        name = board_utils.normalize_name(
            tile_data["name"] + tile_data["middle"]
            if tile_data["middle"]
            else tile_data["name"]
        )
        orientation = tile_data["orientation"]
        pixbuf = self.textures.get(name)
        is_hint = tile_data.get("id") == -1
        if pixbuf:
            if is_hint:
                board_utils.draw_pixbuf_with_alpha(
                    cr, x, y, size, pixbuf, orientation, alpha=0.5)
            else:
                board_utils.draw_pixbuf(cr, x, y, size, pixbuf, orientation)
        else:
            cr.set_source_rgb(1, 1, 1)
            cr.rectangle(x, y, size, size)
            cr.fill()

        if board_utils.is_previewed_tile(
            self.game_data.current_tile, tile_data
        ):
            board_utils.draw_preview_grid(cr, x, y, size)
        else:
            if is_hint:
                cr.set_source_rgba(0, 0, 0, 0.5)
            else:
                cr.set_source_rgb(0, 0, 0)

        cr.set_line_width(2)
        cr.rectangle(x, y, size, size)
        cr.stroke()

        is_preview = board_utils.is_previewed_tile(
            self.game_data.current_tile, tile_data
        )

        # ❌ Do NOT draw real meeples on preview tile
        if not is_preview:
            board_utils.draw_meeples(
                cr,
                x,
                y,
                size,
                self.game_data.game.get_meeples_data(),
                tile_data["id"],
                self.game_data.game.players,
            )
        # Draw preview meeple if this is the previewed tile and meeple_pos is
        # set
        current_tile = self.game_data.current_tile

        if (
            current_tile
            and current_tile.meeple_pos
            and board_utils.is_previewed_tile(current_tile, tile_data)
        ):
            string_to_pos = {
                "NW": (0, 0),
                "N": (0, 1),
                "NE": (0, 2),
                "W": (1, 0),
                "C": (1, 1),
                "E": (1, 2),
                "SW": (2, 0),
                "S": (2, 1),
                "SE": (2, 2),
            }
            row, col = string_to_pos.get(
                self.game_data.current_tile.meeple_pos, (1, 1))
            cell = size / 3
            cx = x + col * cell
            cy = y + row * cell
            padding = cell * 0.2
            current_player = self.game_data.game.get_current_player()
            color = current_player.get_color()
            r, g, b = board_utils.color_map.get(color, (1, 0, 0))
            cr.set_source_rgba(r, g, b, 0.7)  # Semi-transparent for preview
            cr.set_line_width(3)
            cr.move_to(cx + padding, cy + padding)
            cr.line_to(cx + cell - padding, cy + cell - padding)
            cr.move_to(cx + cell - padding, cy + padding)
            cr.line_to(cx + padding, cy + cell - padding)
            cr.stroke()

        # Draw hint meeple if this is the hint tile and meeple is set
        if is_hint and tile_data.get("meeple"):
            string_to_pos = {
                "N": (0, 1),
                "E": (1, 2),
                "S": (2, 1),
                "W": (1, 0),
            }
            row, col = string_to_pos.get(tile_data["meeple"], (1, 1))
            cell = size / 3
            cx = x + col * cell
            cy = y + row * cell
            padding = cell * 0.2
            # Use gray color for hint meeple
            cr.set_source_rgba(0.5, 0.5, 0.5, 0.8)  # Gray semi-transparent
            cr.set_line_width(3)
            cr.move_to(cx + padding, cy + padding)
            cr.line_to(cx + cell - padding, cy + cell - padding)
            cr.move_to(cx + cell - padding, cy + padding)
            cr.line_to(cx + padding, cy + cell - padding)
            cr.stroke()

        if border_color:
            cr.set_source_rgb(*border_color)
            cr.set_line_width(2)
            cr.rectangle(x + 3, y + 3, size - 6, size - 6)
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
        vertex_id, side = self.game_data.game.get_close_neighbors(
            grid_x, grid_y
        )
        if vertex_id is None or side is None:
            self.queue_draw()
            return

        orientation = self.game_data.current_orientation
        move_str = (
            f"{self.game_data.current_tile.current_tile}/"
            f"{vertex_id}{['N', 'E', 'S', 'W'][side]}{orientation}"
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
        return board_utils.click_within_current_tile(
            mouse_x,
            mouse_y,
            offsets,
            self.tile_size,
            self.game_data.current_tile,
        )

    def _meeple_zone(self, mouse_x, mouse_y) -> str:
        offsets = self.get_board_offsets()
        return board_utils.meeple_zone(
            mouse_x,
            mouse_y,
            offsets,
            self.tile_size,
            self.game_data.current_tile,
        )

    def on_drop(self, controller, value, x, y):
        """Handle a tile name string dropped on the board.

        The preview widget already implements a Gtk.DragSource, so this
        method is the corresponding destination handler.  We translate the
        pointer coordinates to a grid location exactly as the click/release
        handlers do, storing the move string and tile coordinates.  Meeple
        placement remains a separate click after the drop.
        """
        grid_x, grid_y = self.pixel_to_grid(x, y)
        vertex_id, side = self.game_data.game.get_close_neighbors(
            grid_x, grid_y
        )
        if vertex_id is not None and side is not None:
            orientation = self.game_data.current_orientation
            move_str = (
                f"{self.game_data.current_tile.current_tile}/"
                f"{vertex_id}{['N', 'E', 'S', 'W'][side]}{orientation}"
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
        return True

    def on_drag_enter(self, controller, x, y):
        """Handle drag entering the board area."""
        if self.game_data.current_tile:
            self.game_data.is_dragging = True
            self.ghost_x = x
            self.ghost_y = y
            self.queue_draw()
            self.grab_focus()
            return Gdk.DragAction.MOVE
        return 0

    def on_drag_motion(self, controller, x, y):
        """Handle drag motion over the board."""
        if self.game_data.is_dragging:
            self.ghost_x = x
            self.ghost_y = y
            self.queue_draw()
            self.grab_focus()
        return Gdk.DragAction.MOVE

    def on_drag_leave(self, controller):
        """Handle drag leaving the board area."""
        self.game_data.is_dragging = False
        self.ghost_x = None
        self.ghost_y = None
        self.grab_focus()
        self.queue_draw()

    def on_key_press(self, controller, keyval, keycode, state):
        step = 20
        if keyval == Gdk.KEY_z:  # up
            self.offset_y += step
        elif keyval == Gdk.KEY_s:  # down
            self.offset_y -= step
        elif keyval == Gdk.KEY_q:  # left
            self.offset_x += step
        elif keyval == Gdk.KEY_d:  # right
            self.offset_x -= step
        elif keyval == Gdk.KEY_r:
            self.game_data.rotate_current_tile()
        else:
            return False

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
        return (
            base_offset_x + self.offset_x,
            base_offset_y + self.offset_y,
            min_x,
            min_y,
        )

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

        vertex_id, side = self.game_data.game.get_close_neighbors(
            grid_x, grid_y
        )

        if vertex_id is not None and side is not None:
            orientation = self.game_data.current_orientation
            move_str = (
                f"{self.game_data.current_tile.current_tile}/{vertex_id}"
                f"{['N', 'E', 'S', 'W'][side]}{orientation}"
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
