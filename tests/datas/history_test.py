from carcassonne.datas.history import History, MoveRecord


def test_move_record_stores_player_and_ai_metadata() -> None:
    record = MoveRecord("CFFF/0N0", player_id=3, is_ai=True)

    assert record.move_str == "CFFF/0N0"
    assert record.player_id == 3
    assert record.is_ai_move is True


def test_history_push_pop_clear_and_list_are_consistent() -> None:
    history = History()
    first = MoveRecord("CFFF/0N0", player_id=0)
    second = MoveRecord("FFFF/m/1E0", player_id=1, is_ai=True)

    history.push_past(first)
    history.push_past(second)
    history.push_future(first)

    assert history.list_history() == ["0:CFFF/0N0;", "1:FFFF/m/1E0;"]
    assert history.pop_past() is second
    assert history.pop_future() is first

    history.push_future(second)
    history.clear_future()
    assert history.future_moves == []

    history.clear_history()
    assert history.past_moves == []
    assert history.future_moves == []
