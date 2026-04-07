from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from carcassonne.business_logic.game import Game
from carcassonne.datas.graph_data import GraphData


def test_play_ai_turn_uses_current_hand_for_minimax_search(monkeypatch):
    monkeypatch.setattr(
        "carcassonne.business_logic.game.game_data.r.shuffle",
        lambda players: None,
    )

    game = Game(
        GraphData(),
        2,
        {
            "ai_mode": "minimax",
            "ai_time": 1,
            "ai_minimax_depth": 2,
            "num_ai_players": 1,
        },
    )
    game.game_data.current_player_order_list = 1
    game.game_data.current_hand = "CRRF"

    played_moves = []

    class FakeExpectimaxPlayer:
        def __init__(
            self,
            game_state,
            start_time,
            max_time,
            depth,
            eval_name="",
        ):
            self.depth_max = depth

        def search(
            self,
            game_state,
            depth,
            alpha,
            beta,
            player_to_max,
            next_player,
        ):
            assert game_state.game_data.current_hand == "CRRF"
            return 0.0, "CRRF/0N0"

    def fake_play_move(move):
        played_moves.append(move)
        game.game_data.current_hand = None
        return True

    monkeypatch.setattr(
        "carcassonne.business_logic.ai_model.ExpectimaxPlayer",
        FakeExpectimaxPlayer,
    )
    monkeypatch.setattr(game, "play_move", fake_play_move)
    monkeypatch.setattr(game, "tick_blitz", lambda: False)
    monkeypatch.setattr(game, "end_game", lambda: False)
    monkeypatch.setattr(
        game.blitz_manager,
        "_ensure_current_player_playable",
        lambda: True,
    )

    game.play_ai_turn(game)

    assert played_moves == ["CRRF/0N0"]
    assert game.game_data.current_hand is None


def test_game_wrapper_methods_delegate_to_underlying_services() -> None:
    game = Game.__new__(Game)
    current_player = SimpleNamespace(get_id=lambda: 4)
    history = SimpleNamespace(
        future_moves=[1],
        list_history=lambda: ["0:CFFF/0N0;"],
        clear_future=Mock(),
    )
    game.game_data = SimpleNamespace(
        history=history,
        game_configuration=SimpleNamespace(settings={}, save_config=Mock()),
        get_game_configuration=lambda: {"ai_mode": "random"},
        get_maximum_number_of_players=lambda: 5,
        get_minimum_number_of_players=lambda: 2,
        get_number_of_players=lambda: 3,
        add_players=Mock(),
        number_of_ai_players=1,
        players_order=[4, 1, 2],
        get_current_player=lambda: current_player,
        start_load_game=Mock(),
        add_online_players=Mock(),
        shuffle_players_order=Mock(),
        extract_tile_code=Mock(return_value="CFFF"),
        graph=SimpleNamespace(
            find_neighbor_at=lambda x, y: (x + 1, y + 1),
            get_adjacent_position=lambda vertex_id, side: (vertex_id + 1, side + 1),
            get_vertices_data=lambda: {1: {"id": 1}},
            get_vertex_data=Mock(),
            get_meeples=lambda: [SimpleNamespace(player_id=0, tile_id=1)],
        ),
    )
    game.save_handler = SimpleNamespace(
        save_game_to_file=Mock(return_value=1),
        load_game_from_file=Mock(return_value=2),
    )
    game.deck_manager = SimpleNamespace(
        draw_tile=Mock(return_value="tile"),
        shuffle_deck=Mock(return_value=7),
    )
    game.new_game = SimpleNamespace(
        start_online_game=Mock(return_value="online"),
        start_new_game=Mock(return_value=None),
    )
    game.end_game_manager = SimpleNamespace(end_game=Mock(return_value=True))
    game.undo_redo_manager = SimpleNamespace(undo=Mock(), redo=Mock())
    game.commands = SimpleNamespace(provide_hint=Mock(return_value="hint"))
    game.blitz_manager = SimpleNamespace(
        get_all_players_remaining_time_seconds=Mock(return_value=[(4, 12.0)]),
        get_player_remaining_time_seconds=Mock(return_value=9.0),
        tick_blitz=Mock(return_value=False),
        get_timeout_message=Mock(return_value="timeout"),
    )
    game.game_mode_manager = SimpleNamespace(
        get_configured_blitz_minutes=Mock(return_value=15),
        get_mode=Mock(return_value="blitz"),
        reset_for_current_state=Mock(),
        has_playable_player=Mock(return_value=True),
        advance_to_next_playable_player=Mock(return_value=True),
        skip_current_player=Mock(return_value=True),
        ensure_current_player_playable=Mock(return_value=True),
    )

    assert game._configured_blitz_minutes() == 15
    assert game._is_blitz_enabled() is True
    game._initialize_mode_state()
    game._initialize_blitz_state()
    assert game._has_playable_player() is True
    assert game._advance_to_next_playable_player() is True
    assert game.skip_current_player() is True
    assert game._ensure_current_player_playable() is True
    game.start_load_game()
    assert game.get_history() == ["0:CFFF/0N0;"]
    game.clear_undo_history()
    assert game.is_undo_history_empty() is False
    assert game.get_game_configuration() == {"ai_mode": "random"}
    game.save_config()
    game.set_game_configuration("timeout", 12)
    game.set_game_configuration("other", "value")
    assert game.get_maximum_number_of_players() == 5
    assert game.get_minimum_number_of_players() == 2
    assert game.get_number_of_players() == 3
    game.set_number_of_ai_players(2)
    game.add_players(1)
    assert game.get_number_of_ai_players() == 2
    assert game.get_players_order() == [4, 1, 2]
    assert game.get_current_player() is current_player
    assert game.save_game_to_file("save.json") == 1
    assert game.load_game_from_file("save.json") == 2
    assert game.start_online_game(["p1"]) == "online"
    game.add_online_players(["p2"])
    assert game.draw_tile(silent=True) == "tile"
    assert game.shuffle_deck("naive", 5) == 7
    game.shuffle_players_order()
    assert game.get_board_data() == [{"id": 1}]
    assert game.get_tile_data("1") is None
    assert game.get_meeples_data() == [{"player_id": 0, "tile_id": 1}]
    assert game.get_close_neighbors(2, 3) == (3, 4)
    assert game.end_game() is True
    game.undo()
    game.redo()
    assert game.provide_hint() == "hint"
    assert game.get_adjacent_position(2, 3) == (3, 4)
    assert game.get_all_players_remaining_time_seconds() == [(4, 12.0)]
    assert game.get_current_player_remaining_time_seconds() == 9.0
    assert game.get_player_remaining_time_seconds(9) == 9.0
    assert game.tick_blitz() is False
    assert game.get_timeout_message() == "timeout"

    game.game_mode_manager.reset_for_current_state.assert_called()
    game.game_data.start_load_game.assert_called_once_with()
    history.clear_future.assert_called_once_with()
    game.game_data.game_configuration.save_config.assert_called_once_with()
    game.game_data.add_players.assert_any_call(2)
    game.game_data.add_players.assert_any_call(1)
    game.game_data.add_online_players.assert_called_once_with(["p2"])
    game.deck_manager.draw_tile.assert_called_once_with(silent=True)
    game.deck_manager.shuffle_deck.assert_called_once_with("naive", 5)
    game.new_game.start_new_game.assert_not_called()
    game.undo_redo_manager.undo.assert_called_once_with()
    game.undo_redo_manager.redo.assert_called_once_with()


def test_rotate_generate_board_and_printed_board_helpers_work_with_simple_vertices() -> None:
    game = Game.__new__(Game)

    class DummyMeeple:
        def __init__(self, tile_id: int, player_id: int, label: str) -> None:
            self.tile_id = tile_id
            self.player_id = player_id
            self.label = label

        def get_position_label(self) -> str:
            return self.label

    class DummyVertex:
        def __init__(self, vertex_id: int, name: str, middle: str, position) -> None:
            self.vertex_id = vertex_id
            self.name = name
            self.middle = middle
            self.position = position

        def get_name(self):
            return self.name

        def get_id(self):
            return self.vertex_id

        def get_middle(self):
            return self.middle

        def get_position(self):
            return self.position

    vertex = DummyVertex(1, "CFRR", "", (0, 0))
    graph = SimpleNamespace(
        get_vertex_orientation=lambda vertex_id: 1,
        get_meeples=lambda: [
            DummyMeeple(1, 7, "N"),
            DummyMeeple(1, 3, "C"),
        ],
        get_vertices=lambda: {1: vertex},
    )
    game.game_data = SimpleNamespace(graph=graph)

    assert game.rotate_dirs(["N", "E", "S", "W"], 1) == ["W", "N", "E", "S"]
    ascii_tile = game.generate_tile_ascii(vertex)
    assert len(ascii_tile) == 3
    assert "[1/3]" in ascii_tile[1]

    game.generate_tile_ascii = lambda v: ["top", "mid", "bot"]
    assert game.get_board() == [vertex]
    assert "top" in game.get_printed_board()

    first_render = game.get_printed_board()
    second_render = game.get_printed_board()
    assert first_render == second_render
    assert vertex.middle == ""

    empty_game = Game.__new__(Game)
    empty_game.game_data = SimpleNamespace(
        graph=SimpleNamespace(get_vertices=lambda: {})
    )
    assert empty_game.get_board() is None
    assert empty_game.get_printed_board() == "No vertices.\n"


def build_play_move_game(
    *,
    timed_out=False,
    playable=True,
    current_hand="CFFF",
    current_player_id=0,
    expected_player_id=0,
    meeples=1,
    rules_ok=True,
):
    game = Game.__new__(Game)
    player = SimpleNamespace(
        get_id=lambda: current_player_id,
        get_meeples=lambda: meeples,
        __str__=lambda self: "player",
    )
    added_moves = []
    river_updates = []
    game.tick_blitz = lambda: timed_out
    game.blitz_manager = SimpleNamespace(
        _ensure_current_player_playable=lambda: playable
    )
    game.river_manager = SimpleNamespace(
        update_river_turn=lambda parts: river_updates.append(parts)
    )
    game.game_data = SimpleNamespace(
        players_order=[expected_player_id],
        current_player_order_list=0,
        current_hand=current_hand,
        extract_tile_code=lambda move: move.split("/")[0],
        rules_manager=SimpleNamespace(
            check_move=lambda *args, **kwargs: rules_ok
        ),
        board=SimpleNamespace(
            add_tile_to_board=lambda *args, **kwargs: added_moves.append(args[0])
        ),
        graph=SimpleNamespace(get_vertices=lambda: {}),
        tiles_info=object(),
        history=object(),
        players={current_player_id: player},
        get_current_player=lambda: player,
        get_number_of_players=lambda: 1,
    )
    game.get_current_player = lambda: player
    game.get_number_of_players = lambda: 1
    return game, added_moves, river_updates


def test_play_move_covers_validation_failures_and_success() -> None:
    game, _, _ = build_play_move_game(timed_out=True)
    assert game.play_move("CFFF/0N0") is False

    game, _, _ = build_play_move_game(playable=False)
    assert game.play_move("CFFF/0N0") is False

    game, _, _ = build_play_move_game(expected_player_id=2)
    assert game.play_move("CFFF/0N0") is False

    game, _, _ = build_play_move_game(current_hand=None)
    assert game.play_move("CFFF/0N0") is False

    game, _, _ = build_play_move_game(current_hand="FRFR")
    assert game.play_move("CFFF/0N0") is False

    game, _, _ = build_play_move_game()
    assert game.play_move("not-a-move") is False

    game, _, _ = build_play_move_game(meeples=0)
    assert game.play_move("CFFF/0N0/N") is False

    game, _, _ = build_play_move_game(rules_ok=False)
    assert game.play_move("CFFF/0N0") is False

    game, added_moves, river_updates = build_play_move_game()
    assert game.play_move("CFFF/0N0") is True
    assert added_moves == ["CFFF/0N0"]
    assert river_updates == [["CFFF", "0N0"]]
    assert game.game_data.current_hand is None
    assert game.game_data.current_player_order_list == 0


def test_play_ai_turn_rejects_missing_game_and_falls_back_when_meeples_are_gone(
    monkeypatch,
):
    game = Game.__new__(Game)
    ai_player = SimpleNamespace(
        get_id=lambda: 0,
        get_username=lambda: "AI",
        is_ai_player=lambda: True,
        get_meeples=lambda: 0,
    )
    played_moves = []

    game.tick_blitz = lambda: False
    game.end_game = lambda: False
    game.play_move = lambda move: played_moves.append(move) or move == "CFFF/0N0"
    game.blitz_manager = SimpleNamespace(
        _ensure_current_player_playable=lambda: True
    )
    game.deck_manager = SimpleNamespace(
        draw_tile=lambda silent=True: setattr(game.game_data, "current_hand", "CFFF")
    )
    game.game_data = SimpleNamespace(
        current_hand=None,
        get_current_player=lambda: ai_player,
        get_game_configuration=lambda: {"ai_mode": "random", "ai_time": 5},
    )
    game.get_current_player = lambda: ai_player
    game.get_game_configuration = lambda: {"ai_mode": "random", "ai_time": 5}

    class FakeRandomPlayer:
        def random_move(self, hand, game_state):
            return "CFFF/0N0/N"

    monkeypatch.setattr(
        "carcassonne.business_logic.ai_model.RandomPlayer",
        FakeRandomPlayer,
    )

    with pytest.raises(ValueError, match="game parameter is required"):
        game.play_ai_turn()

    game.play_ai_turn(game)

    assert played_moves == ["CFFF/0N0/N", "CFFF/0N0"]
