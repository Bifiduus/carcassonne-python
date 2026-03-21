"""Encapsulate the little tile preview picture and its interaction logic.

Rather than sprinkling drag/rotate/pressed code inside :class:`GameGUI`,
this widget knows how to present and gum up the feedback for the currently
held tile.  It delegates higher-level logic (e.g. what happens when the
user clicks the preview) back to the owning ``GameGUI`` instance.
"""

from gi.repository import Gtk, Gdk, GdkPixbuf
from carcassonne.presentation.gui.utils import tile_image_path
import gi

gi.require_version("Gtk", "4.0")


class TilePreview(Gtk.Picture):
    def __init__(self, gui):
        super().__init__()
        self.gui = gui

        # basic geometry
        self.set_can_shrink(True)
        self.set_keep_aspect_ratio(True)
        self.set_size_request(100, 100)
        self.set_hexpand(False)
        self.set_vexpand(False)

        # interaction
        click = Gtk.GestureClick()
        click.connect("pressed", self._on_pressed)
        self.add_controller(click)

        self._setup_drag_source()

    # public helper methods -------------------------------------------------
    def set_tile(self, tile_name: str):
        """Show ``tile_name`` in the preview area without rotation."""
        image_path = tile_image_path(tile_name)
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=image_path,
            width=100,
            height=100,
            preserve_aspect_ratio=True,
        )
        self.set_paintable(Gdk.Texture.new_for_pixbuf(pixbuf))

    def update_rotation(self):
        """Apply the current orientation stored in ``gui.game_data``."""
        if not self.gui.game_data.current_tile:
            return
        image_path = tile_image_path(
            self.gui.game_data.current_tile.current_tile
        )
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=image_path,
            width=100,
            height=100,
            preserve_aspect_ratio=True,
        )
        rotated = pixbuf.rotate_simple(
            [
                GdkPixbuf.PixbufRotation.NONE,
                GdkPixbuf.PixbufRotation.CLOCKWISE,
                GdkPixbuf.PixbufRotation.UPSIDEDOWN,
                GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE,
            ][self.gui.game_data.current_orientation]
        )
        self.set_paintable(Gdk.Texture.new_for_pixbuf(rotated))

    # internal helpers -------------------------------------------------------
    def _setup_drag_source(self):
        # Set up proper GTK drag source for native drag and drop
        drag_source = Gtk.DragSource.new()
        drag_source.set_actions(Gdk.DragAction.MOVE)
        drag_source.connect("prepare", self._on_drag_prepare)
        drag_source.connect("drag-begin", self._on_drag_begin)
        drag_source.connect("drag-end", self._on_drag_end)
        self.add_controller(drag_source)

        # Keep click gesture for immediate visual feedback
        click = Gtk.GestureClick()
        click.connect("pressed", self._on_pressed)
        click.connect("released", self._on_released)
        self.add_controller(click)

    def _on_pressed(self, gesture, n_press, x, y):
        if self.gui.game_data.current_tile:
            self.gui.game_data.is_dragging = True
            self.gui.board_view.grab_focus()
            self.gui.board_view.queue_draw()

    def _on_released(self, gesture, n_press, x, y):
        # le release se fait sur le board, pas ici
        pass

    def _on_drag_prepare(self, source, x, y):
        if not self.gui.game_data.current_tile:
            return None
        # pass the tile name string so drops can pick it up
        return Gdk.ContentProvider.new_for_value(
            self.gui.game_data.current_tile.current_tile
        )

    def _on_drag_begin(self, drag_source, drag):
        if not self.gui.game_data.current_tile:
            return

        image_path = tile_image_path(
            self.gui.game_data.current_tile.current_tile
        )
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            filename=image_path,
            width=100,
            height=100,
            preserve_aspect_ratio=True,
        )
        rotations = [
            GdkPixbuf.PixbufRotation.NONE,
            GdkPixbuf.PixbufRotation.CLOCKWISE,
            GdkPixbuf.PixbufRotation.UPSIDEDOWN,
            GdkPixbuf.PixbufRotation.COUNTERCLOCKWISE,
        ]
        rotated = pixbuf.rotate_simple(
            rotations[self.gui.game_data.current_orientation]
        )
        texture = Gdk.Texture.new_for_pixbuf(rotated)

        # keep a reference so the texture isn't garbage-collected
        self._drag_texture = texture
        # Set a transparent icon to hide drag feedback
        transparent_pixbuf = GdkPixbuf.Pixbuf.new(
            GdkPixbuf.Colorspace.RGB, True, 8, 1, 1
        )
        transparent_pixbuf.fill(0x00000000)  # Fully transparent
        transparent_texture = Gdk.Texture.new_for_pixbuf(transparent_pixbuf)
        drag_source.set_icon(transparent_texture, 0, 0)

    def _on_drag_end(self, drag_source, drag, *args):
        self.gui.board_view.grab_focus()
