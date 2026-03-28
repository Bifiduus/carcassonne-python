from carcassonne.business_logic.game import Game
from carcassonne.datas.graph_data import GraphData


def test_play_ai_turn_discards_unplayable_tile_before_search(monkeypatch):
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
    game.current_player_order_list = 1
    game.current_hand = "CCFF"
    game.deck.tiles = ["CRRF"]

    played_moves = []
    discarded_count_before = game.tiles_info.tiles_count["CCFF"]

    class FakeRandomPlayer:
        def get_possible_moves(self, tile, game_state):
            if tile == "CCFF":
                return []
            if tile == "CRRF":
                return ["CRRF/0N0"]
            return []

        def random_move(self, tile, game_state):
            return self.get_possible_moves(tile, game_state)[0]

    class FakeExpectimaxPlayer:
        def __init__(self, game_state, start_time, max_time, depth):
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
            assert game_state.current_hand == "CRRF"
            return 0.0, "CRRF/0N0"

    def fake_play_move(move):
        played_moves.append(move)
        game.current_hand = None
        return True

    monkeypatch.setattr(
        "carcassonne.business_logic.ai_model.RandomPlayer",
        FakeRandomPlayer,
    )
    monkeypatch.setattr(
        "carcassonne.business_logic.ai_model.ExpectimaxPlayer",
        FakeExpectimaxPlayer,
    )
    monkeypatch.setattr(game, "play_move", fake_play_move)

    game.play_ai_turn()

    assert played_moves == ["CRRF/0N0"]
    assert game.tiles_info.tiles_count["CCFF"] == discarded_count_before
    assert game.current_hand is None
    assert "CCFF" in game.deck.tiles
