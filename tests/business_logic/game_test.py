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
