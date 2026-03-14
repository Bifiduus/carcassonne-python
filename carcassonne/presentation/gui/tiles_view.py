class TilesView():
    def __init__(self, tile_name: str, tile_id: int = 0) -> None:
        # name of the tile that is currently held by the player
        self.current_tile = tile_name
        # unique identifier for preview/placement (used by parse_move)
        self.id = tile_id
        # move string produced when tile is placed (e.g. "XX/12N0")
        self.move = ''
        self.x = 0
        self.y = 0
        # orientation (0..3) of the held tile
        self.orientation = 0
        # where the meeple will be placed ("N","C","SE" etc.)
        self.meeple_pos = ''

    def playable_tile(self):
        if self.meeple_pos != '':
            return self.move + '/' + self.meeple_pos
        return self.move

    def parse_move(self, move, x, y):
        # move string may be either "name/..." or "name/middle/..." depending on
        # whether the tile has a middle symbol
        if move.count('/') == 1:
            name, rest = move.split("/")
            orientation = int(rest[-1])
            middle = ""
        else:
            name, middle, rest = move.split("/")
            orientation = int(rest[-1])

        return {
            "id": self.id,
            "x": x,
            "y": y,
            "name": name,
            "middle": middle,
            "orientation": orientation
        }
