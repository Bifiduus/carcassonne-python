import pytest

from carcassonne.datas.meeple_data import Meeple


def test_meeple_position_label_and_repr_are_human_readable() -> None:
    meeple = Meeple(player_id=2, tile_id=7, position=0, lands_components="R3")

    assert meeple.get_position_label() == "N"
    assert "player=2" in repr(meeple)
    assert "pos=N" in repr(meeple)


def test_meeple_post_init_rejects_invalid_positions() -> None:
    meeple = Meeple(player_id=1, tile_id=4, position=9, lands_components="C1")

    with pytest.raises(ValueError):
        meeple.__post_init__()
