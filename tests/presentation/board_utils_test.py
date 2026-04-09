"""Tests for board_utils module - GUI helper functions for coordinate calculations."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

pytest.importorskip("gi")

from carcassonne.presentation.gui import board_utils  # noqa: E402


class TestNormalizeName:
    """Test tile name normalization for texture cache lookups."""

    def test_normalize_name_with_slash(self) -> None:
        assert board_utils.normalize_name("CFFF/12N1") == "CFFF12N1"

    def test_normalize_name_without_slash(self) -> None:
        assert board_utils.normalize_name("CFFF") == "CFFF"

    def test_normalize_name_with_different_tiles(self) -> None:
        assert board_utils.normalize_name("CDFF/5E1") == "CDFF5E1"
        assert board_utils.normalize_name("RRRR") == "RRRR"


class TestClickWithinCurrentTile:
    """Test mouse click detection within the current tile."""

    def test_click_within_tile_returns_true_for_inside_click(self) -> None:
        current_tile = SimpleNamespace(x=0, y=0)
        offsets = (0, 0, 0, 0)  # offset_x, offset_y, min_x, min_y
        tile_size = 100
        mouse_x, mouse_y = 50, 50

        result = board_utils.click_within_current_tile(
            mouse_x, mouse_y, offsets, tile_size, current_tile
        )

        assert result is True

    def test_click_within_tile_returns_false_for_outside_click(self) -> None:
        current_tile = SimpleNamespace(x=0, y=0)
        offsets = (0, 0, 0, 0)
        tile_size = 100
        mouse_x, mouse_y = 150, 150

        result = board_utils.click_within_current_tile(
            mouse_x, mouse_y, offsets, tile_size, current_tile
        )

        assert result is False

    def test_click_within_tile_with_offsets(self) -> None:
        current_tile = SimpleNamespace(x=1, y=1)
        offsets = (50, 50, 0, 0)  # offset_x, offset_y, min_x, min_y
        tile_size = 100
        # Click on tile at (1, 1): pixel at 50 + 100 = 150 to 250
        mouse_x, mouse_y = 200, 200

        result = board_utils.click_within_current_tile(
            mouse_x, mouse_y, offsets, tile_size, current_tile
        )

        assert result is True

    def test_click_within_tile_at_boundary(self) -> None:
        current_tile = SimpleNamespace(x=0, y=0)
        offsets = (0, 0, 0, 0)
        tile_size = 100
        # Test exact boundaries
        assert board_utils.click_within_current_tile(
            0, 0, offsets, tile_size, current_tile) is True
        assert board_utils.click_within_current_tile(
            100, 100, offsets, tile_size, current_tile) is True
        assert board_utils.click_within_current_tile(
            101, 100, offsets, tile_size, current_tile) is False


class TestMeepleZone:
    """Test meeple position detection within a clicked tile."""

    def test_meeple_zone_northwest(self) -> None:
        current_tile = SimpleNamespace(x=0, y=0)
        offsets = (0, 0, 0, 0)
        tile_size = 100
        mouse_x, mouse_y = 16, 16  # First third of tile

        zone = board_utils.meeple_zone(
            mouse_x, mouse_y, offsets, tile_size, current_tile
        )

        assert zone == "NW"

    def test_meeple_zone_center(self) -> None:
        current_tile = SimpleNamespace(x=0, y=0)
        offsets = (0, 0, 0, 0)
        tile_size = 100
        mouse_x, mouse_y = 50, 50  # Center

        zone = board_utils.meeple_zone(
            mouse_x, mouse_y, offsets, tile_size, current_tile
        )

        assert zone == "C"

    def test_meeple_zone_southeast(self) -> None:
        current_tile = SimpleNamespace(x=0, y=0)
        offsets = (0, 0, 0, 0)
        tile_size = 100
        mouse_x, mouse_y = 83, 83  # Last third

        zone = board_utils.meeple_zone(
            mouse_x, mouse_y, offsets, tile_size, current_tile
        )

        assert zone == "SE"

    def test_meeple_zone_north(self) -> None:
        current_tile = SimpleNamespace(x=0, y=0)
        offsets = (0, 0, 0, 0)
        tile_size = 100
        mouse_x, mouse_y = 50, 16  # Top center

        zone = board_utils.meeple_zone(
            mouse_x, mouse_y, offsets, tile_size, current_tile
        )

        assert zone == "N"

    def test_meeple_zone_east(self) -> None:
        current_tile = SimpleNamespace(x=0, y=0)
        offsets = (0, 0, 0, 0)
        tile_size = 100
        mouse_x, mouse_y = 83, 50  # Right center

        zone = board_utils.meeple_zone(
            mouse_x, mouse_y, offsets, tile_size, current_tile
        )

        assert zone == "E"


class TestIsPreviewedTile:
    """Test detection of the currently previewed tile."""

    def test_is_previewed_tile_returns_true_for_matching_tile(self) -> None:
        current_tile = SimpleNamespace(x=1, y=2, move="CFFF/5N0")
        tile_data = {"x": 1, "y": 2}

        result = board_utils.is_previewed_tile(current_tile, tile_data)

        assert result is True

    def test_is_previewed_tile_returns_false_for_empty_move(self) -> None:
        current_tile = SimpleNamespace(x=1, y=2, move="")
        tile_data = {"x": 1, "y": 2}

        result = board_utils.is_previewed_tile(current_tile, tile_data)

        assert result is False

    def test_is_previewed_tile_returns_false_for_different_coordinates(self) -> None:
        current_tile = SimpleNamespace(x=1, y=2, move="CFFF/5N0")
        tile_data = {"x": 2, "y": 3}

        result = board_utils.is_previewed_tile(current_tile, tile_data)

        assert result is False

    def test_is_previewed_tile_returns_false_when_no_current_tile(self) -> None:
        # The function returns (current_tile and ...) so None returns None (falsy)
        result = board_utils.is_previewed_tile(None, {"x": 1, "y": 2})
        assert not result  # Check for falsy value (None)


class TestColorMap:
    """Test color mapping for meeples."""

    def test_color_map_has_expected_colors(self) -> None:
        assert board_utils.color_map["red"] == (1, 0, 0)
        assert board_utils.color_map["blue"] == (0, 0, 1)
        assert board_utils.color_map["yellow"] == (1, 1, 0)
        assert board_utils.color_map["white"] == (0.9, 0.9, 0.9)
        assert board_utils.color_map["green"] == (0, 1, 0)
        assert board_utils.color_map["black"] == (0, 0, 0)


class TestMeeplePosGrids:
    """Test meeple position grid mappings."""

    def test_meeple_pos_grid_contains_all_9_positions(self) -> None:
        expected_positions = ["NW", "N", "NE", "W", "C", "E", "SW", "S", "SE"]
        assert all(
            pos in board_utils.MEEPLE_POS_GRID for pos in expected_positions)

    def test_meeple_pos_grid_values(self) -> None:
        assert board_utils.MEEPLE_POS_GRID["NW"] == (0, 0)
        assert board_utils.MEEPLE_POS_GRID["C"] == (1, 1)
        assert board_utils.MEEPLE_POS_GRID["SE"] == (2, 2)

    def test_meeple_pos_cardinal_contains_4_directions(self) -> None:
        expected_directions = ["N", "E", "S", "W"]
        assert all(
            d in board_utils.MEEPLE_POS_CARDINAL for d in expected_directions)

    def test_meeple_pos_cardinal_values(self) -> None:
        assert board_utils.MEEPLE_POS_CARDINAL["N"] == (0, 1)
        assert board_utils.MEEPLE_POS_CARDINAL["E"] == (1, 2)
        assert board_utils.MEEPLE_POS_CARDINAL["W"] == (1, 0)


class DummyPixbuf:
    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height

    def get_width(self) -> int:
        return self.width

    def get_height(self) -> int:
        return self.height


class DummyCairoContext:
    def __init__(self) -> None:
        self.calls = []

    def save(self) -> None:
        self.calls.append(("save",))

    def restore(self) -> None:
        self.calls.append(("restore",))

    def translate(self, x, y) -> None:
        self.calls.append(("translate", x, y))

    def rotate(self, angle) -> None:
        self.calls.append(("rotate", angle))

    def scale(self, sx, sy) -> None:
        self.calls.append(("scale", sx, sy))

    def paint_with_alpha(self, alpha) -> None:
        self.calls.append(("paint_with_alpha", alpha))

    def set_source_rgb(self, r, g, b) -> None:
        self.calls.append(("set_source_rgb", r, g, b))

    def set_line_width(self, width) -> None:
        self.calls.append(("set_line_width", width))

    def move_to(self, x, y) -> None:
        self.calls.append(("move_to", x, y))

    def line_to(self, x, y) -> None:
        self.calls.append(("line_to", x, y))

    def stroke(self) -> None:
        self.calls.append(("stroke",))


def test_rotate_meeple_label_respects_orientation_steps() -> None:
    assert board_utils._rotate_meeple_label("N", 0) == "N"
    assert board_utils._rotate_meeple_label("N", 1) == "E"
    assert board_utils._rotate_meeple_label("NE", 2) == "SW"
    assert board_utils._rotate_meeple_label("C", 3) == "C"


def test_draw_preview_grid_draws_two_vertical_and_two_horizontal_lines() -> None:
    cr = DummyCairoContext()

    board_utils.draw_preview_grid(cr, x=10, y=20, size=90)

    assert ("set_source_rgb", 0, 1, 0) in cr.calls
    assert ("set_line_width", 1) in cr.calls
    assert cr.calls.count(("move_to", 40.0, 20)) == 1
    assert cr.calls.count(("line_to", 40.0, 110)) == 1
    assert cr.calls.count(("move_to", 70.0, 20)) == 1
    assert cr.calls.count(("line_to", 70.0, 110)) == 1


def test_draw_pixbuf_with_alpha_applies_transform_and_alpha(monkeypatch) -> None:
    cr = DummyCairoContext()
    pixbuf = DummyPixbuf(width=50, height=25)
    gdk_call = Mock()
    monkeypatch.setattr(board_utils.Gdk, "cairo_set_source_pixbuf", gdk_call)

    board_utils.draw_pixbuf_with_alpha(
        cr,
        x=10,
        y=20,
        size=100,
        pixbuf=pixbuf,
        orientation=1,
        alpha=0.4,
    )

    assert ("translate", 60.0, 70.0) in cr.calls
    assert ("scale", 2.0, 4.0) in cr.calls
    assert ("paint_with_alpha", 0.4) in cr.calls
    gdk_call.assert_called_once_with(cr, pixbuf, -25.0, -12.5)


def test_draw_pixbuf_wrapper_uses_opaque_alpha(monkeypatch) -> None:
    wrapped_call = Mock()
    monkeypatch.setattr(board_utils, "draw_pixbuf_with_alpha", wrapped_call)

    board_utils.draw_pixbuf(
        cr=object(),
        x=1,
        y=2,
        size=3,
        pixbuf=object(),
        orientation=2,
    )

    assert wrapped_call.call_args.args[-1] == 1.0


def test_draw_meeples_draws_only_target_tile_and_uses_color_fallback() -> None:
    cr = DummyCairoContext()
    players = {
        0: SimpleNamespace(get_color=lambda: "blue"),
        1: SimpleNamespace(get_color=lambda: "unknown"),
    }
    meeples = [
        {"tile_id": 7, "position": 0, "player_id": 0},
        {"tile_id": 7, "position": 2, "player_id": 1},
        {"tile_id": 8, "position": 4, "player_id": 0},
    ]

    board_utils.draw_meeples(
        cr,
        x=0,
        y=0,
        size=90,
        meeples=meeples,
        tile_id=7,
        players=players,
        orientation=0,
    )

    # One set_source_rgb call per meeple on target tile only (2 meeples).
    set_colors = [call for call in cr.calls if call[0] == "set_source_rgb"]
    assert len(set_colors) == 2
    assert ("set_source_rgb", 0, 0, 1) in set_colors
    assert ("set_source_rgb", 1, 0, 0) in set_colors
