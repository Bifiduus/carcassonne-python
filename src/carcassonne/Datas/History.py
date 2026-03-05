"""This module defines the History class, which is responsible for managing the history of moves made during a game of Carcassonne. 
The History class maintains two lists: one for past moves and one for future moves (used for undo functionality). 
It provides methods to push and pop moves from these lists, as well as to clear the future moves when a new move is made.
"""
from carcassonne.Datas.Serializer import build_str

class MoveRecord:
    def __init__(self, move_str, player_id=1, is_ai: bool=False):
        self.move_str = move_str
        self.player_id = player_id
        self.is_ai_move = is_ai


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
        return [build_str(record) for record in self.past_moves]
