"""This module defines the History class, which is responsible for managing the history of moves made during a game of Carcassonne. 
The History class maintains two lists: one for past moves and one for future moves (used for undo functionality). 
It provides methods to push and pop moves from these lists, as well as to clear the future moves when a new move is made.
"""
class MoveRecord:
    def __init__(self, move_str, player_id=1):
        self.move_str = move_str
        self.player_id = player_id


class History:
    def __init__(self):
        self.past_moves = []
        self.future_moves = []

    def push_past(self, record: MoveRecord):
        self.past_moves.append(record)

    def push_future(self, record: MoveRecord):
        self.future_moves.append(record)

    def pop_past(self) -> MoveRecord:
        return self.past_moves.pop()
    
    def pop_future(self) -> MoveRecord:
        return self.future_moves.pop()
    
    def clear_future(self):
        self.future_moves.clear()

    def clear_history(self):
        self.past_moves.clear()
        self.future_moves.clear()

    def list_history(self):
        return [record.move_str for record in self.past_moves]
