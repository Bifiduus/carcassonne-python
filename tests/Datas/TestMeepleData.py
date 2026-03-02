import pytest
from carcassonne.Datas.MeepleData import Meeple

class TestMeepleData:
    def test_meeple_data_init(self):
        meeple = Meeple(1, 1, 0, 'R1')
        assert meeple is not None
        assert meeple.player_id == 1, "Player ID should be set correctly"
        assert meeple.tile_id == 1, "Tile ID should be set correctly"
        assert meeple.position == 0, "Position should be set correctly"
        assert meeple.lands_components == 'R1', "Lands components should be set correctly"
        assert meeple.get_position_label() == 'N', "Position label should be 'N' for position 0"

    def test_meeple_data_invalid_position(self):
        try:
            Meeple(1, 1, 9, 'R1').__post_init__()  # Manually call __post_init__ to trigger validation
            assert False, "Creating a Meeple with an invalid position should raise ValueError"
        except ValueError as e:
            assert str(e) == "Position must be between 0 and 8, got 9", "Error message should indicate invalid position"

    def test_meeple_data_repr(self):
        meeple = Meeple(1, 1, 0, 'R1')
        expected_repr = "Meeple(player=1, tile=1, pos=N, lands_components=R1)"
        assert repr(meeple) == expected_repr, "Meeple __repr__ should return the expected string representation"