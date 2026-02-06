class MoveRecord:
    def __init__(self, move_str, player_id, tile_sides, target_id, target_side, rotation, meeple=None):
        self.move_str = move_str
        self.player_id = player_id
        self.tile_sides = tile_sides
        self.target_id = target_id
        self.target_side = target_side
        self.rotation = rotation
        self.meeple = meeple


class History:
    def __init__(self) -> None:
        self.past_moves = []
        self.future_moves = []


