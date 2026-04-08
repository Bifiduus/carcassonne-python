"""Tests for TilesView - Tile placement and data representation."""

from carcassonne.presentation.gui.tiles_view import TilesView


class TestTilesViewInitialization:
    """Test TilesView initialization with different parameters."""

    def test_tiles_view_default_initialization(self) -> None:
        tile = TilesView("CFFF")

        assert tile.current_tile == "CFFF"
        assert tile.id == 0
        assert tile.move == ""
        assert tile.x == 0
        assert tile.y == 0
        assert tile.orientation == 0
        assert tile.meeple_pos == ""

    def test_tiles_view_with_custom_id(self) -> None:
        tile = TilesView("CDFF", tile_id=42)

        assert tile.current_tile == "CDFF"
        assert tile.id == 42

    def test_tiles_view_with_different_tile_names(self) -> None:
        tile_names = ["CFFF", "CDFF", "RRRR", "CCCC"]

        for name in tile_names:
            tile = TilesView(name)
            assert tile.current_tile == name


class TestPlayableTile:
    """Test tile placement string generation."""

    def test_playable_tile_without_meeple(self) -> None:
        tile = TilesView("CFFF")
        tile.move = "CFFF/12N0"
        tile.meeple_pos = ""

        result = tile.playable_tile()

        assert result == "CFFF/12N0"

    def test_playable_tile_with_meeple(self) -> None:
        tile = TilesView("CFFF")
        tile.move = "CFFF/12N0"
        tile.meeple_pos = "SE"

        result = tile.playable_tile()

        assert result == "CFFF/12N0/SE"

    def test_playable_tile_with_different_positions(self) -> None:
        tile = TilesView("CFFF")
        tile.move = "CFFF/12N0"
        positions = ["N", "E", "S", "W", "C", "NW", "NE", "SW", "SE"]

        for pos in positions:
            tile.meeple_pos = pos
            result = tile.playable_tile()
            assert result == f"CFFF/12N0/{pos}"


class TestParseMove:
    """Test parsing move strings with various formats."""

    def test_parse_move_without_middle(self) -> None:
        tile = TilesView("CFFF", tile_id=5)

        result = tile.parse_move("CFFF/12E2", 1, 2)

        assert result["id"] == 5
        assert result["x"] == 1
        assert result["y"] == 2
        assert result["name"] == "CFFF"
        assert result["middle"] == ""
        assert result["orientation"] == 2

    def test_parse_move_with_middle(self) -> None:
        tile = TilesView("CDFF", tile_id=10)

        result = tile.parse_move("CDFF/C/15S1", 3, 4)

        assert result["id"] == 10
        assert result["x"] == 3
        assert result["y"] == 4
        assert result["name"] == "CDFF"
        assert result["middle"] == "C"
        assert result["orientation"] == 1

    def test_parse_move_with_all_orientations(self) -> None:
        tile = TilesView("CFFF")

        # Test all 4 orientations (0, 1, 2, 3)
        for orientation in range(4):
            result = tile.parse_move(f"CFFF/5N{orientation}", 0, 0)
            assert result["orientation"] == orientation

    def test_parse_move_with_different_vertices(self) -> None:
        tile = TilesView("CFFF", tile_id=1)

        for vertex in range(1, 10):
            for side in ["N", "E", "S", "W"]:
                move_str = f"CFFF/{vertex}{side}0"
                result = tile.parse_move(move_str, 5, 6)
                assert result["name"] == "CFFF"
                assert result["orientation"] == 0

    def test_parse_move_with_different_coordinates(self) -> None:
        tile = TilesView("CFFF")

        coordinates = [(0, 0), (1, 2), (10, 20), (-5, 3)]
        for x, y in coordinates:
            result = tile.parse_move("CFFF/5N0", x, y)
            assert result["x"] == x
            assert result["y"] == y


class TestTileStateModification:
    """Test modification of tile state."""

    def test_set_move_and_coordinates(self) -> None:
        tile = TilesView("CFFF")

        tile.move = "CFFF/12S1"
        tile.x = 5
        tile.y = 10
        tile.orientation = 2

        assert tile.move == "CFFF/12S1"
        assert tile.x == 5
        assert tile.y == 10
        assert tile.orientation == 2

    def test_reset_meeple_position(self) -> None:
        tile = TilesView("CFFF")
        tile.meeple_pos = "C"

        tile.meeple_pos = ""

        assert tile.meeple_pos == ""
        assert tile.playable_tile() == tile.move

    def test_change_meeple_position_multiple_times(self) -> None:
        tile = TilesView("CFFF")
        tile.move = "CFFF/12N0"
        positions = ["N", "E", "S"]

        for pos in positions:
            tile.meeple_pos = pos
            assert tile.playable_tile() == f"CFFF/12N0/{pos}"
