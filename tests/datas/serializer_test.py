import pytest

from carcassonne.datas import serializer
from carcassonne.datas.history import MoveRecord


class TestSerializer:
    def test_parse_move(self):
        move_str = "FFFF/m/1N0"
        expected_output = {
            "tile_sides": 'FFFF',
            "center": 'm',
            "target_id": 1,
            "target_side": 'N',
            "rotation": 0,
            "meeple": None,
        }
        assert serializer.parse_move(
            move_str) == expected_output, "Parsed move should match expected output"
        with pytest.raises(ValueError):
            serializer.parse_move("Random")
        with pytest.raises(ValueError):
            serializer.parse_move("FFFF")
        with pytest.raises(ValueError):
            serializer.parse_move("FFFFF")
        with pytest.raises(ValueError):
            serializer.parse_move("FFF")
        with pytest.raises(ValueError):
            serializer.parse_move("FFFF/m/1N")
        with pytest.raises(ValueError):
            serializer.parse_move("FFFF/m/1N0X")
        with pytest.raises(ValueError):
            serializer.parse_move("FFFF/m/1N0/EXTRA")
        with pytest.raises(ValueError):
            serializer.parse_move("FFFF/m/1N5")
        with pytest.raises(ValueError):
            serializer.parse_move("FFFF/m/1X0")
        with pytest.raises(ValueError):
            serializer.parse_move("FFFF/m/1N0/X/EXTRA")

    def test_build_str(self):

        record = MoveRecord(player_id=1, move_str="FFFF/m/1N0;")
        expected_output = "1:FFFF/m/1N0;"
        assert serializer.build_str(
            record) == expected_output, "Built string should match expected output"
