import pytest

from carcassonne.datas.tiles_info import TilesInfo


def test_tile_inventory_methods_update_counts_and_validate_unknown_tiles() -> None:
    tiles_info = TilesInfo()
    initial_count = tiles_info.tiles_count["CFFF"]

    assert tiles_info.is_tile_left("CFFF") is True

    tiles_info.remove_tile("CFFF")
    assert tiles_info.tiles_count["CFFF"] == initial_count - 1

    tiles_info.add_tile("CFFF")
    assert tiles_info.tiles_count["CFFF"] == initial_count

    with pytest.raises(ValueError, match="Invalid tile code"):
        tiles_info.add_tile("UNKNOWN")

    tiles_info.tiles_count["CFFF"] = 0
    assert tiles_info.is_tile_left("CFFF") is False

    with pytest.raises(ValueError, match="No tiles left of type"):
        tiles_info.remove_tile("CFFF")
