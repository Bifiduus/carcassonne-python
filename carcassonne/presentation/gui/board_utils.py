"""Helper functions extracted from BoardView to keep it slim.

This module contains pure utilities for normalizing tile names, doing
coordinate math, and drawing common GUI elements such as meeples and
preview grids.  The idea is that ``BoardView`` can simply delegate to
these helpers without holding too much implementation detail.
"""

import os
import math
from typing import Any, Dict, Tuple

import gi
gi.require_version("Gdk", "4.0")
gi.require_version("GdkPixbuf", "2.0")
from gi.repository import Gdk, GdkPixbuf

color_map = {
    "red": (1, 0, 0),
    "blue": (0, 0, 1),
    "yellow": (1, 1, 0),
    "white": (0.9, 0.9, 0.9),
    "green": (0, 1, 0),
}


def normalize_name(name: str) -> str:
    """Return the key used in texture cache for a given tile identifier."""
    if "/" in name:
        parts = name.split("/")
        return f"{parts[0]}{parts[1]}"
    return name


def click_within_current_tile(
    mouse_x: float,
    mouse_y: float,
    offsets: Tuple[int, int, int, int],
    tile_size: float,
    current_tile,
) -> bool:
    """Return True if the pixel click lies inside the currently held tile."""
    offset_x, offset_y, min_x, min_y = offsets
    lx = current_tile.x
    ly = current_tile.y
    tile_px = offset_x + (lx - min_x) * tile_size
    tile_py = offset_y + (ly - min_y) * tile_size
    return (
        tile_px <= mouse_x <= tile_px + tile_size
        and tile_py <= mouse_y <= tile_py + tile_size
    )


def meeple_zone(
    mouse_x: float,
    mouse_y: float,
    offsets: Tuple[int, int, int, int],
    tile_size: float,
    current_tile,
) -> str:
    """Convert a click inside a tile into a meeple position string."""
    offset_x, offset_y, min_x, min_y = offsets
    lx = current_tile.x
    ly = current_tile.y
    tile_px = offset_x + (lx - min_x) * tile_size
    tile_py = offset_y + (ly - min_y) * tile_size
    cell = tile_size / 3
    col = int((mouse_x - tile_px) // cell)
    row = int((mouse_y - tile_py) // cell)
    positions = [
        ["NW", "N", "NE"],
        ["W", "C", "E"],
        ["SW", "S", "SE"],
    ]
    return positions[row][col]


def draw_pixbuf_with_alpha(
    cr, x, y, size, pixbuf, orientation: int, alpha: float = 1.0
) -> None:
    """Draw a tile pixbuf rotated and scaled with optional transparency.

    ``alpha`` defaults to 1.0 for an opaque tile; lower values produce a
    translucent "ghost" effect.  This consolidates the common cairo
    transformation logic used throughout ``BoardView``.
    """
    cr.save()
    angle = orientation * 90
    cr.translate(x + size / 2, y + size / 2)
    cr.rotate(math.radians(angle))
    scale_x = size / pixbuf.get_width()
    scale_y = size / pixbuf.get_height()
    cr.scale(scale_x, scale_y)
    Gdk.cairo_set_source_pixbuf(
        cr, pixbuf, -pixbuf.get_width() / 2, -pixbuf.get_height() / 2
    )
    cr.paint_with_alpha(alpha)
    cr.restore()


def draw_pixbuf(cr, x, y, size, pixbuf, orientation: int) -> None:
    """Backward‑compatible wrapper used by existing callers."""
    draw_pixbuf_with_alpha(cr, x, y, size, pixbuf, orientation, 1.0)


def is_previewed_tile(current_tile, tile_data: Dict[str, Any]) -> bool:
    return (
        current_tile
        and current_tile.x == tile_data["x"]
        and current_tile.y == tile_data["y"]
        and current_tile.move != ""
    )


def draw_preview_grid(cr, x, y, size) -> None:
    cr.set_source_rgb(0, 1, 0)
    cr.set_line_width(1)
    cell = size / 3
    # vertical
    cr.move_to(x + cell, y)
    cr.line_to(x + cell, y + size)
    cr.move_to(x + 2 * cell, y)
    cr.line_to(x + 2 * cell, y + size)
    # horizontal
    cr.move_to(x, y + cell)
    cr.line_to(x + size, y + cell)
    cr.move_to(x, y + 2 * cell)
    cr.line_to(x + size, y + 2 * cell)


def draw_meeples(cr, x, y, size, meeples, tile_id, players) -> None:
    for m in meeples:
        if m["tile_id"] != tile_id:
            continue
        position_map = {
            7: (0, 0),
            0: (0, 1),
            1: (0, 2),
            6: (1, 0),
            8: (1, 1),
            2: (1, 2),
            5: (2, 0),
            4: (2, 1),
            3: (2, 2),
        }
        row, col = position_map.get(m["position"], (1, 1))
        cell = size / 3
        cx = x + col * cell
        cy = y + row * cell
        padding = cell * 0.2
        player = players[m["player_id"]]
        color = player.get_color()
        r, g, b = color_map.get(color, (1, 0, 0))
        cr.set_source_rgb(r, g, b)
        cr.set_line_width(3)
        cr.move_to(cx + padding, cy + padding)
        cr.line_to(cx + cell - padding, cy + cell - padding)
        cr.move_to(cx + cell - padding, cy + padding)
        cr.line_to(cx + padding, cy + cell - padding)
        cr.stroke()
