from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import pytest

import carcassonne.business_logic.ai.mcts_player as mcts_module
from carcassonne.business_logic.ai.mcts_player import MCTSNode, MCTSPlayer
from carcassonne.datas.history import History, MoveRecord


class DummyScore:
    def __init__(self, score: int = 0) -> None:
        self.score = score

    def set_points(self, points: int) -> None:
        self.score = points


class DummyPlayer:
    def __init__(
        self, player_id: int, meeples: int = 2, score: int = 0
    ) -> None:
        self.player_id = player_id
        self.meeples = meeples
        self.score = DummyScore(score)

    def get_id(self) -> int:
        return self.player_id

    def get_meeples(self) -> int:
        return self.meeples

    def get_score(self) -> DummyScore:
        return self.score

    def get_score_int(self) -> int:
        return self.score.score


class DummyVertex:
    def __init__(self, free_directions: set[int]) -> None:
        self.free_directions = free_directions

    def is_neighbor_free(self, direction: int) -> bool:
        return direction in self.free_directions


class DummyGraph:
    def __init__(self, vertices: dict[int, DummyVertex] | None = None) -> None:
        self._vertices = vertices or {0: DummyVertex({0})}
        self._meeples = {"origin": 1}
        self.lands_components = {"before": [1]}
        self.next_set_id = 2
        self.set_meeples_calls: list[dict] = []

    def get_vertices(self) -> dict[int, DummyVertex]:
        return self._vertices

    def get_meeples(self) -> dict:
        return self._meeples

    def set_meeples(self, meeples: dict) -> None:
        self.set_meeples_calls.append(meeples)
        self._meeples = meeples


class DummyDeck:
    def __init__(self) -> None:
        self.tiles = ["NEXT"]
        self.river_tiles = ["RIVER"]
        self.append_calls: list[str] = []

    def append(self, tile: str) -> None:
        self.append_calls.append(tile)
        self.tiles.append(tile)


class DummyRulesManager:
    def __init__(self, allowed_moves: set[str]) -> None:
        self.allowed_moves = allowed_moves
        self.checked_moves: list[tuple[str, int]] = []

    def check_move(
        self,
        move: str,
        graph,
        river_manager,
        current_player_id: int,
    ) -> bool:
        self.checked_moves.append((move, current_player_id))
        return move in self.allowed_moves


class DummyBoard:
    def __init__(self) -> None:
        self.scored_components = {"before"}
        self.added_moves: list[str] = []
        self.removed_moves: list[str] = []

    def add_tile_to_board(
        self,
        move: str,
        graph,
        tiles_info,
        history: History,
        players: dict[int, DummyPlayer],
        players_order,
        current_player: DummyPlayer,
    ) -> None:
        self.added_moves.append(move)
        history.push_past(MoveRecord(move, current_player.get_id()))
        current_player.get_score().score += 4
        if move.count("/") >= 2:
            current_player.meeples -= 1
        self.scored_components = {"after"}
        graph.lands_components = {"after": [2]}
        graph.next_set_id = 8

    def remove_tile_from_board(
        self,
        move_str: str,
        graph,
        tiles_info,
        history,
        players,
    ) -> None:
        self.removed_moves.append(move_str)
        self.scored_components = {"removed"}


class DummyGameData:
    def __init__(
        self,
        allowed_moves: set[str],
        *,
        meeples: int = 1,
        current_hand: str = "CFFF",
    ) -> None:
        self.graph = DummyGraph()
        self.tiles_info = SimpleNamespace(
            direction_dict={"N": 0},
            tiles_count={"CFFF": 1},
        )
        self.rules_manager = DummyRulesManager(allowed_moves)
        self.players = {
            0: DummyPlayer(0, meeples=meeples, score=12),
            1: DummyPlayer(1, meeples=2, score=7),
        }
        self.players_order = [0, 1]
        self.current_player_order_list = 0
        self.history = History()
        self.board = DummyBoard()
        self.current_hand = current_hand
        self.deck = DummyDeck()

    def get_current_player(self) -> DummyPlayer:
        current_id = self.players_order[self.current_player_order_list]
        return self.players[current_id]

    def extract_tile_code(self, move: str) -> str | None:
        if not isinstance(move, str) or "/" not in move:
            return None
        return move.split("/")[0]


class DummyGame:
    def __init__(
        self,
        allowed_moves: set[str],
        *,
        meeples: int = 1,
        current_hand: str = "CFFF",
    ) -> None:
        self.game_data = DummyGameData(
            allowed_moves,
            meeples=meeples,
            current_hand=current_hand,
        )
        self.river_manager = SimpleNamespace(
            river_active=True,
            river_previous_opposite_direction=2,
            river_turn=3,
        )
        self.draws = ["DRAWN"]
        self.terminal_flag = False

    def get_current_player(self) -> DummyPlayer:
        return self.game_data.get_current_player()

    def get_number_of_players(self) -> int:
        return len(self.game_data.players)

    def draw_tile(self, silent: bool = False) -> str | None:
        if not self.draws:
            return None
        drawn = self.draws.pop(0)
        self.game_data.current_hand = drawn
        return drawn


class StaticNode:
    def __init__(
        self,
        *,
        state=None,
        move: str = "CFFF/0N0",
        visits: int = 1,
        total_reward: float = 0.0,
        children: list | None = None,
        untried_moves: list | None = None,
        parent=None,
    ) -> None:
        self._state = state
        self._move = move
        self._visits = visits
        self._total_reward = total_reward
        self._children = children or []
        self._untried_moves = untried_moves or []
        self._parent = parent
        self.visits_added = 0
        self.reward_added = 0.0

    def get_state(self):
        return self._state

    def get_move(self):
        return self._move

    def get_visits(self) -> int:
        return self._visits

    def get_total_reward(self) -> float:
        return self._total_reward

    def get_children(self) -> list:
        return self._children

    def get_untried_moves(self) -> list:
        return self._untried_moves

    def get_parent(self):
        return self._parent

    def add_visitor(self, number: int) -> None:
        self.visits_added += number

    def add_reward(self, reward: float) -> None:
        self.reward_added += reward


class FakeScalarPrediction:
    def __init__(self, value: float) -> None:
        self.value = value

    def __float__(self) -> float:
        raise TypeError("use item")

    def item(self) -> float:
        return self.value


def create_player(game: DummyGame) -> MCTSPlayer:
    return MCTSPlayer(
        game=game,
        start_time=0.0,
        max_time=100.0,
        eval_fn=lambda node: node,
    )


def test_mcts_node_exposes_state_and_accumulates_stats() -> None:
    game = DummyGame(set())
    fake_player = SimpleNamespace(
        get_possible_moves=lambda tile, game: ["move-a", "move-b"]
    )

    node = MCTSNode(
        game=game,
        mcts_player=fake_player,
        parent="parent",
        move="move-a",
        player="player-0",
    )
    node.add_visitor(2)
    node.add_reward(1.5)

    assert node.get_state() is game
    assert node.get_parent() == "parent"
    assert node.get_move() == "move-a"
    assert node.get_player() == "player-0"
    assert node.get_children() == []
    assert node.get_untried_moves() == ["move-a", "move-b"]
    assert node.get_visits() == 2
    assert node.get_total_reward() == 1.5


def test_set_evaluation_method_and_terminal_behaviour() -> None:
    player = create_player(DummyGame(set()))
    custom_eval = lambda node: "custom"

    player.set_evaluation_method(custom_eval)
    assert player.eval_fn is custom_eval

    player.set_evaluation_method("UCT")
    assert player.eval_fn.__name__ == "uct_select_child"

    player.set_evaluation_method("ML")
    assert player.eval_fn.__name__ == "ml_select_child"

    with pytest.raises(ValueError):
        player.set_evaluation_method("bad-mode")

    assert player.terminal(SimpleNamespace(tiles_count={"CFFF": 0})) is True
    assert player.terminal(SimpleNamespace(tiles_count={"CFFF": 1})) is False


def test_load_ml_model_handles_cached_attempted_missing_success_and_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cached_player = create_player(DummyGame(set()))
    cached_player.ml_model = object()
    assert cached_player._load_ml_model() is True

    attempted_player = create_player(DummyGame(set()))
    attempted_player._ml_model_attempted = True
    assert attempted_player._load_ml_model() is False

    missing_player = create_player(DummyGame(set()))
    fake_models = ModuleType("keras.models")
    fake_models.load_model = lambda path: object()
    fake_keras = ModuleType("keras")
    fake_keras.models = fake_models
    monkeypatch.setitem(sys.modules, "keras", fake_keras)
    monkeypatch.setitem(sys.modules, "keras.models", fake_models)
    monkeypatch.setattr(mcts_module.os.path, "exists", lambda path: False)
    assert missing_player._load_ml_model() is False

    loaded_model = object()
    success_player = create_player(DummyGame(set()))
    fake_models.load_model = lambda path: loaded_model
    monkeypatch.setattr(mcts_module.os.path, "exists", lambda path: True)
    assert success_player._load_ml_model() is True
    assert success_player.ml_model is loaded_model

    failing_player = create_player(DummyGame(set()))

    def raise_on_load(path: str):
        raise RuntimeError("boom")

    fake_models.load_model = raise_on_load
    assert failing_player._load_ml_model() is False
    assert failing_player.ml_model is None


def test_extract_ml_features_encodes_reward_state_and_meeple_usage() -> None:
    game = DummyGame(set())
    player = create_player(game)
    parent = StaticNode(visits=10)
    child = StaticNode(
        state=game,
        move="CFFF/0N0/NW",
        visits=3,
        total_reward=9.0,
        children=[object()],
        untried_moves=["next"],
    )

    features = player._extract_ml_features(parent, child)

    assert features[:5] == [3.0, 9.0, 3.0, 10.0, 1.0]
    assert features[5:9] == [1.0, 1.0, 12.0, 1.0]
    assert features[9] > 0.0


def test_ml_select_child_raises_on_leaf_and_falls_back_when_needed() -> None:
    player = create_player(DummyGame(set()))
    leaf = StaticNode(children=[])

    with pytest.raises(ValueError):
        player.ml_select_child(leaf)

    fallback_child = StaticNode(state=DummyGame(set()))
    fallback_node = StaticNode(children=[fallback_child])
    player._load_ml_model = lambda: False
    player.uct_select_child = lambda node, c=1.41: "fallback"
    assert player.ml_select_child(fallback_node) == "fallback"

    player._load_ml_model = lambda: True
    player.ml_model = SimpleNamespace(
        predict=lambda features, verbose=0: (_ for _ in ()).throw(
            RuntimeError("predict failed")
        )
    )
    assert player.ml_select_child(fallback_node) == "fallback"


def test_ml_select_child_uses_predictions_with_multiple_value_shapes() -> None:
    player = create_player(DummyGame(set()))
    child_a = StaticNode(
        state=DummyGame(set()),
        move="CFFF/0N0",
        visits=2,
        total_reward=2.0,
    )
    child_b = StaticNode(
        state=DummyGame(set()),
        move="CFFF/0N0/NW",
        visits=1,
        total_reward=1.0,
    )
    node = StaticNode(children=[child_a, child_b], visits=5)

    player._load_ml_model = lambda: True
    player._extract_ml_features = lambda node, child: [1.0]
    player.ml_model = SimpleNamespace(
        predict=lambda features, verbose=0: [
            [0.2],
            FakeScalarPrediction(0.8),
        ]
    )

    assert player.ml_select_child(node) is child_b


@pytest.mark.parametrize(
    ("meeples", "allowed_moves", "expected"),
    [
        (0, {"CFFF/0N0"}, ["CFFF/0N0"]),
        (1, {"CFFF/0N0/NW"}, ["CFFF/0N0/NW"]),
    ],
)
def test_get_possible_moves_filters_legal_moves(
    meeples: int, allowed_moves: set[str], expected: list[str]
) -> None:
    game = DummyGame(allowed_moves, meeples=meeples)
    player = create_player(game)

    assert player.get_possible_moves("CFFF", game) == expected


def test_uct_select_child_prefers_unvisited_then_best_scored_child() -> None:
    player = create_player(DummyGame(set()))
    unvisited = StaticNode(visits=0, total_reward=0.0)
    visited = StaticNode(visits=3, total_reward=9.0)
    node = StaticNode(children=[visited, unvisited], visits=10)

    assert player.uct_select_child(node) is unvisited

    better = StaticNode(visits=2, total_reward=8.0)
    worse = StaticNode(visits=4, total_reward=4.0)
    scored_node = StaticNode(children=[worse, better], visits=20)

    assert player.uct_select_child(scored_node, c=0.1) is better


def test_expand_consumes_one_untried_move_and_creates_a_child() -> None:
    game = DummyGame(set())
    player = create_player(game)
    player.get_possible_moves = lambda tile, game: []
    played_moves: list[str] = []

    def fake_play(game: DummyGame, move: str) -> bool:
        played_moves.append(move)
        return True

    player.play_move_for_ai = fake_play
    root = StaticNode(state=game, untried_moves=["move-a"], children=[])

    child = player.expand(root)

    assert played_moves == ["move-a"]
    assert root.get_untried_moves() == []
    assert root.get_children() == [child]
    assert child.get_parent() is root
    assert child.get_move() == "move-a"


def test_rollout_retries_dead_hands_until_a_move_is_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game = DummyGame(set(), current_hand="CFFF")
    player = create_player(game)
    player.end_time = 10.0
    player.terminal = lambda tiles_info: game.terminal_flag
    player.get_possible_moves = (
        lambda tile, game: [] if tile == "CFFF" else ["DRAWN/0N0"]
    )

    def fake_play(game: DummyGame, move: str) -> bool:
        game.terminal_flag = True
        return True

    player.play_move_for_ai = fake_play
    monkeypatch.setattr(mcts_module.random, "choice", lambda moves: moves[0])
    monkeypatch.setattr(mcts_module.time, "time", lambda: 0.0)

    assert player.rollout(game) == 1
    assert game.game_data.deck.append_calls == ["CFFF"]


def test_rollout_stops_when_no_new_tile_can_be_drawn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    game = DummyGame(set(), current_hand="CFFF")
    game.draws = []
    player = create_player(game)
    player.end_time = 10.0
    player.terminal = lambda tiles_info: False
    player.get_possible_moves = lambda tile, game: []
    monkeypatch.setattr(mcts_module.time, "time", lambda: 0.0)

    assert player.rollout(game) == 0
    assert game.game_data.deck.append_calls == ["CFFF"]


def test_compute_reward_and_backpropagate_restore_along_the_path() -> None:
    game = DummyGame(set())
    player = create_player(game)
    root = StaticNode(state=game, parent=None)
    child = StaticNode(state=game, parent=root)
    undo_calls: list[str] = []
    player.undo_for_ai = lambda state: undo_calls.append("undo")

    assert player.compute_reward(game, 0) == 5

    player.backpropagate(child, reward=4.5, counter=2)

    assert child.visits_added == 1
    assert child.reward_added == 4.5
    assert undo_calls == ["undo", "undo", "undo"]


def test_mcts_returns_a_fallback_root_move_when_no_child_was_expanded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeRootNode:
        def __init__(self, game, mcts_player) -> None:
            self.children = []
            self.untried_moves = ["move-a", "move-b"]

    monkeypatch.setattr(mcts_module, "MCTSNode", FakeRootNode)
    monkeypatch.setattr(mcts_module.random, "choice", lambda moves: moves[-1])
    monkeypatch.setattr(mcts_module.time, "time", lambda: 0.0)

    game = DummyGame(set())
    player = create_player(game)
    player.end_time = -1.0

    assert player.mcts(game) == "move-b"


def test_mcts_returns_the_best_expanded_child_and_restores_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeChild:
        def __init__(self, move: str, reward: float, visits: int) -> None:
            self.move = move
            self.reward = reward
            self.visits = visits

        def get_total_reward(self) -> float:
            return self.reward

        def get_visits(self) -> int:
            return self.visits

        def get_move(self) -> str:
            return self.move

    class FakeRootNode:
        def __init__(self, game, mcts_player) -> None:
            self.children = [
                FakeChild("move-a", reward=2.0, visits=1),
                FakeChild("move-b", reward=6.0, visits=2),
            ]
            self.untried_moves = []

    monkeypatch.setattr(mcts_module, "MCTSNode", FakeRootNode)
    monkeypatch.setattr(mcts_module.time, "time", lambda: 0.0)

    game = DummyGame(set(), current_hand="CFFF")
    player = create_player(game)
    player.end_time = -1.0

    assert player.mcts(game) == "move-b"
    assert game.game_data.current_hand == "CFFF"
    assert game.game_data.graph.set_meeples_calls[-1] == {"origin": 1}


def test_play_move_for_ai_and_undo_restore_state_and_deck() -> None:
    game = DummyGame({"CFFF/0N0/NW"}, meeples=1, current_hand="CFFF")
    player = create_player(game)
    original_player = game.get_current_player()
    original_score = original_player.get_score_int()
    original_meeples = original_player.get_meeples()

    assert player.play_move_for_ai(game, "CRRF/0N0") is False
    assert player.play_move_for_ai(game, "CFFF/0N0/NW") is True
    assert game.game_data.current_hand is None
    assert game.game_data.current_player_order_list == 1
    assert game.game_data.history.past_moves[-1].move_str == "CFFF/0N0/NW"

    player.undo_for_ai(game)

    assert game.game_data.history.past_moves == []
    assert game.game_data.history.future_moves[-1].move_str == "CFFF/0N0/NW"
    assert game.game_data.current_player_order_list == 0
    assert original_player.get_score_int() == original_score
    assert original_player.get_meeples() == original_meeples
    assert game.game_data.board.removed_moves == ["0:CFFF/0N0/NW;"]
    assert game.game_data.deck.tiles[-1] == "CFFF"
    assert game.game_data.graph.lands_components == {"before": [1]}
    assert game.game_data.graph.next_set_id == 2
