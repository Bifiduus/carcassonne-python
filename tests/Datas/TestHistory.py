import pytest
from carcassonne.Datas.History import History, MoveRecord

class TestHistory:
    def test_history_init(self):
        history = History()
        assert history.past_moves == [], "Past moves should be initialized as an empty list"
        assert history.future_moves == [], "Future moves should be initialized as an empty list"
    
    def test_push_and_pop_moves(self):
        history = History()
        move1 = "RRRR"
        move2 = "RRFF"
        record1 = MoveRecord(move_str=move1, player_id=1)
        record2 = MoveRecord(move_str=move2, player_id=2)

        history.push_past(record1)
        history.push_past(record2)

        assert len(history.past_moves) == 2, "Two moves should be in past moves"
        assert history.pop_past() == record2, "The last move popped should be the second move"
        assert history.pop_past() == record1, "The next move popped should be the first move"
        assert len(history.past_moves) == 0, "Past moves should be empty after popping all moves"
        history.push_future(record1)
        assert len(history.future_moves) == 1, "One move should be in future moves"
        assert history.pop_future() == record1, "The move popped from future should be the first move"
        assert len(history.future_moves) == 0, "Future moves should be empty after popping all moves"

    def test_clear_history(self):
        history = History()
        move1 = "RRRR"
        move2 = "RRFF"
        record1 = MoveRecord(move_str=move1, player_id=1)
        record2 = MoveRecord(move_str=move2, player_id=2)

        history.push_past(record1)
        history.push_past(record2)
        history.push_future(record1)

        history.clear_history()
        assert len(history.past_moves) == 0, "Past moves should be empty after clearing history"
        assert len(history.future_moves) == 0, "Future moves should be empty after clearing history"

    def test_list_history(self):
        history = History()
        move1 = "RRRR"
        move2 = "RRFF"
        record1 = MoveRecord(move_str=move1, player_id=1)
        record2 = MoveRecord(move_str=move2, player_id=2)

        history.push_past(record1)
        history.push_past(record2)

        history_list = history.list_history()
        assert len(history_list) == 2, "History list should contain two moves"
        assert history_list[0] == "1:RRRR;", "First move in history list should be from player 1"
        assert history_list[1] == "2:RRFF;", "Second move in history list should be from player 2"