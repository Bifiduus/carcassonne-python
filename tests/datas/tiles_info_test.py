import pytest
from carcassonne.datas.tiles_info import Tile, TilesInfo


class TestTile:
    def test_tile_init(self):
        code = "RRRR"
        connections = {
            'N': 'R1',
            'E': 'R1',
            'S': 'R1',
            'W': 'R1'
        }
        connect_to = {
            'N': ['NE', 'N', 'NW'],
            'E': ['NE', 'E', 'SE'],
            'S': ['SE', 'S', 'SW'],
            'W': ['NW', 'W', 'SW']
        }
        tile_info = Tile(code, connections, connect_to)
        assert tile_info.code == code, "Tile code should be set correctly"
        assert tile_info.tiles_lands == connections, "Tile connections should be set correctly"
        assert tile_info.connect_to == connect_to, "Tile connect_to should be set correctly"


class TestTilesInfo:
    def test_tile_info_creation(self):
        tiles_info = TilesInfo()
        assert tiles_info is not None, "TilesInfo instance should be created successfully"
        assert len(
            tiles_info.tiles_dict) > 0, "TilesInfo should contain tiles definitions"
        assert 'RRRR' in tiles_info.tiles_dict, "Tile 'RRRR' should be defined in TilesInfo"

    def test_rotate_matrix_90(self):
        tiles_info = TilesInfo()
        matrix = [
            ['N', 'NE', 'E'],
            ['NW', 'C', 'SE'],
            ['W', 'SW', 'S']
        ]
        expected_rotated_90 = [
            ['W', 'NW', 'N'],
            ['SW', 'C', 'NE'],
            ['S', 'SE', 'E']
        ]
        rotated_90 = tiles_info.rotate_matrix_90(matrix)
        assert rotated_90 == expected_rotated_90, "Matrix should be rotated 90 degrees correctly"

    def test_is_tile_left(self):
        tiles_info = TilesInfo()
        tiles_info.tiles_count['RRRR'] = 0
        assert tiles_info.is_tile_left(
            'RRRR') == False, "Tile 'RRRR' should not be left when count is 0"
        tiles_info.tiles_count['RRRR'] = 1
        assert tiles_info.is_tile_left(
            'RRRR') == True, "Tile 'RRRR' should be left when count is greater than 0"

    def test_add_tile(self):
        tiles_info = TilesInfo()
        initial_count = tiles_info.tiles_count['RRRR']
        tiles_info.add_tile('RRRR')
        assert tiles_info.tiles_count['RRRR'] == initial_count + \
            1, "Tile count for 'RRRR' should be incremented by 1"
        with pytest.raises(ValueError):
            tiles_info.add_tile('INVALID_TILE')

    def test_remove_tile(self):
        tiles_info = TilesInfo()
        tiles_info.tiles_count['RRRR'] = 1
        tiles_info.remove_tile('RRRR')
        assert tiles_info.tiles_count['RRRR'] == 0, "Tile count for 'RRRR' should be decremented by 1"
        with pytest.raises(ValueError):
            tiles_info.remove_tile('INVALID_TILE')
        with pytest.raises(ValueError):
            tiles_info.remove_tile('RRRR')
