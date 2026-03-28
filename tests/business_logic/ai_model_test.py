import time

from carcassonne.business_logic.ai_model import ExpectimaxPlayer
from carcassonne.business_logic.ai_model import MCTSPlayer


class DummyTilesInfo:
    tiles_count = {"A": 1, "B": 1, "C": 1}


class DummyGameData:
    def __init__(self):
        self.current_hand = "ROOT"
        self.tiles_info = DummyTilesInfo()
        self.players = {0: object(), 1: object()}


class DummyGame:
    def __init__(self):
        self.game_data = DummyGameData()


class DummyMCTSPlayerState:
    def __init__(self, score=0, meeples=7):
        self._score = score
        self._meeples = meeples

    def get_score_int(self):
        return self._score

    def get_meeples(self):
        return self._meeples


class DummyMCTSGame:
    def get_current_player(self):
        return DummyMCTSPlayerState()


class DummyMCTSNode:
    def __init__(self, visits=1, total_reward=0.0, move="CFFF/0N0"):
        self._visits = visits
        self._total_reward = total_reward
        self._children = []
        self._untried_moves = []
        self._move = move
        self._state = DummyMCTSGame()

    def get_children(self):
        return self._children

    def get_untried_moves(self):
        return self._untried_moves

    def get_visits(self):
        return self._visits

    def get_total_reward(self):
        return self._total_reward

    def get_move(self):
        return self._move

    def get_state(self):
        return self._state


class TimeoutProbePlayer(ExpectimaxPlayer):
    def __init__(self, game, start_time, max_time):
        super().__init__(
            game, start_time, max_time, depth=4, eval_fn=self._eval
        )
        self.probe_calls = 0

    def _eval(self, game, player_to_max, next_player):
        return 7.0

    def terminal(self, tiles_info):
        return False

    def num_successors(self, tiles_info):
        return {"A": 1, "B": 1, "C": 1}

    def n_probe(
        self,
        game,
        alpha,
        beta,
        depth,
        player_to_max,
        next_player,
        probingFactor=1,
    ):
        self.probe_calls += 1
        time.sleep(0.03)
        return 1.0

    def search(
        self,
        game,
        depth,
        alpha,
        beta,
        player_to_max,
        next_player,
    ):
        return 0.0, "move"


class ExpiredProbePlayer(ExpectimaxPlayer):
    def __init__(self, game, start_time, max_time):
        super().__init__(
            game, start_time, max_time, depth=2, eval_fn=self._eval
        )
        self.play_calls = 0

    def _eval(self, game, player_to_max, next_player):
        return 11.0

    def get_possible_moves(self, tile, game):
        return ["m1", "m2"]

    def play_move_for_ai(self, game, move):
        self.play_calls += 1
        return True

    def undo_for_ai(self, game):
        return None

    def star25(
        self,
        game,
        depth,
        alpha,
        beta,
        player_to_max,
        next_player,
    ):
        return 3.0


def test_star25_stops_probing_after_timeout_and_restores_hand():
    game = DummyGame()
    player = TimeoutProbePlayer(game, time.time(), 0.01)

    started = time.time()
    value = player.star25(
        game,
        depth=3,
        alpha=float("-inf"),
        beta=float("inf"),
        player_to_max=0,
        next_player=0,
    )
    elapsed = time.time() - started

    assert player.probe_calls == 1
    assert elapsed < 0.07
    assert value > 0
    assert game.game_data.current_hand == "ROOT"


def test_n_probe_returns_eval_without_exploring_when_time_expired():
    game = DummyGame()
    player = ExpiredProbePlayer(game, time.time() - 1, 0.01)

    value = player.n_probe(
        game,
        alpha=float("-inf"),
        beta=float("inf"),
        depth=2,
        player_to_max=0,
        next_player=0,
    )

    assert value == 11.0
    assert player.play_calls == 0


def test_mcts_accepts_ml_selection_name():
    player = MCTSPlayer(DummyGame(), time.time(), 0.1, eval_name="ML")

    assert player.eval_fn == player.ml_select_child


def test_mcts_ml_selection_falls_back_to_uct(monkeypatch):
    player = MCTSPlayer(DummyGame(), time.time(), 0.1, eval_name="ML")
    monkeypatch.setattr(player, "_load_ml_model", lambda: False)

    root = DummyMCTSNode(visits=20)
    child_weak = DummyMCTSNode(visits=10, total_reward=10.0)
    child_strong = DummyMCTSNode(visits=10, total_reward=30.0)
    root.get_children().extend([child_weak, child_strong])

    selected = player.ml_select_child(root)

    assert selected is child_strong
