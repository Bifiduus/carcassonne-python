"""Tests for board_utils module - GUI helper functions for coordinate calculations."""

from carcassonne.presentation.gui import board_utils
import pytest
from types import SimpleNamespace
from unittest.mock import Mock

pytest.importorskip("gi")


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
