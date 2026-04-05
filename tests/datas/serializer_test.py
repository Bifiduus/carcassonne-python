from types import SimpleNamespace

import pytest

from carcassonne.datas.serializer import build_str, parse_move


def test_parse_move_without_center_or_meeple() -> None:
    parsed = parse_move("CFFF/12N3")

    assert parsed == {
        "tile_sides": "CFFF",
        "center": None,
        "target_id": 12,
        "target_side": "N",
        "rotation": 3,
        "meeple": "",
    }


def test_parse_move_with_center_and_meeple() -> None:
    parsed = parse_move("FFFF/m/7E1/SW")

    assert parsed == {
        "tile_sides": "FFFF",
        "center": "m",
        "target_id": 7,
        "target_side": "E",
        "rotation": 1,
        "meeple": "SW",
    }


@pytest.mark.parametrize(
    ("move", "message"),
    [
        (None, "move must be a string"),
        ("CFFF", "move must contain at least tile and placement"),
        ("CFF/0N0", "tile must have 4 sides"),
        ("CFFF/not-a-placement", "invalid placement format"),
        ("CFFF/0N0/INVALID", "invalid meeple format"),
        ("CFFF/0N0/N/extra", "too many parts in move"),
        ("FFFF/m", "invalid placement format"),
    ],
)
def test_parse_move_rejects_invalid_input(move, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        parse_move(move)


def test_build_str_normalizes_existing_trailing_separator() -> None:
    record = SimpleNamespace(player_id=3, move_str="CFFF/0N0;")

    assert build_str(record) == "3:CFFF/0N0;"
