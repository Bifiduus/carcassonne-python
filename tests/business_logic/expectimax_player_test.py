from __future__ import annotations

from types import SimpleNamespace

import pytest

import carcassonne.business_logic.ai.expectimax_player as expectimax_module
from carcassonne.business_logic.ai.expectimax_player import (
    ExpectimaxPlayer,
    IterativeDeepeningPlayer,
)
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
        self.lands_components = {"before": [1]}
        self.next_set_id = 3
        self._meeples = {}

    def get_verticies(self) -> dict[int, DummyVertex]:
        return self._vertices

    def get_meeples(self) -> dict:
        return self._meeples

    def set_meeples(self, meeples: dict) -> None:
        self._meeples = meeples


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
        current_player.get_score().score += 5
        if move.count("/") >= 2:
            current_player.meeples -= 1
        self.scored_components = {"after"}
        graph.lands_components = {"after": [2]}
        graph.next_set_id = 9

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
            tiles_count={"CFFF": 1, "CRRF": 2},
        )
        self.rules_manager = DummyRulesManager(allowed_moves)
        self.players = {
            0: DummyPlayer(0, meeples=meeples, score=10),
            1: DummyPlayer(1, meeples=2, score=4),
        }
        self.players_order = [0, 1]
        self.current_player_order_list = 0
        self.history = History()
        self.board = DummyBoard()
        self.current_hand = current_hand

    def get_current_player(self) -> DummyPlayer:
        current_id = self.players_order[self.current_player_order_list]
        return self.players[current_id]

    def get_number_of_players(self) -> int:
        return len(self.players)

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
        self.river_manager = object()

    def get_current_player(self) -> DummyPlayer:
        return self.game_data.get_current_player()

    def get_number_of_players(self) -> int:
        return self.game_data.get_number_of_players()

    def get_board(self) -> str:
        return "board"


def create_player(game: DummyGame, depth: int = 2) -> ExpectimaxPlayer:
    return ExpectimaxPlayer(
        game=game,
        start_time=0.0,
        max_time=100.0,
        depth=depth,
        eval_fn=lambda game, player_to_max, next_player: 7.0,
    )


def test_set_evaluation_method_supports_names_and_callables() -> None:
    game = DummyGame(set())
    player = create_player(game)

    player.set_evaluation_method("short_term")
    assert player.eval_fn is expectimax_module.short_term_evaluate_state

    player.set_evaluation_method("disruption")
    assert player.eval_fn is expectimax_module.disruption_evaluate_state

    custom_eval = lambda game, player_to_max, next_player: 42.0
    player.set_evaluation_method(custom_eval)
    assert player.eval_fn is custom_eval

    with pytest.raises(ValueError):
        player.set_evaluation_method("unknown")


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


def test_order_moves_prefers_root_hint_then_history() -> None:
    game = DummyGame(set())
    player = ExpectimaxPlayer(
        game,
        start_time=0.0,
        max_time=100.0,
        depth=3,
        eval_fn=lambda game, player_to_max, next_player: 0.0,
        preferred_root_move="move-b",
        history_table={"move-a": 2, "move-c": 5},
    )

    assert player._order_moves(["move-a", "move-b", "move-c"], 3) == [
        "move-b",
        "move-c",
        "move-a",
    ]
    assert player._order_moves(["move-a", "move-b", "move-c"], 2) == [
        "move-c",
        "move-a",
        "move-b",
    ]


def test_search_returns_evaluation_on_terminal_depth_or_timeout() -> None:
    game = DummyGame(set())
    player = create_player(game)
    player.eval_fn = lambda game, player_to_max, next_player: 13.0

    assert player.search(game, 0, -1.0, 1.0, 0, 0) == (13.0, "")

    player.terminal = lambda tiles_info: True
    assert player.search(game, 2, -1.0, 1.0, 0, 0) == (13.0, "")


def test_search_max_branch_selects_best_move_and_tracks_cutoff_history() -> None:
    game = DummyGame(set())
    player = create_player(game, depth=2)
    score_by_move = {"move-a": 1.0, "move-b": 5.0}

    player._time_exceeded = lambda: False
    player.terminal = lambda tiles_info: False
    player.get_possible_moves = lambda tile, game: ["move-a", "move-b"]

    def fake_play(game: DummyGame, move: str) -> bool:
        game.last_move = move
        return True

    player.play_move_for_ai = fake_play
    player.star25 = lambda game, *args: score_by_move[game.last_move]
    player.undo_for_ai = lambda game: None

    score, move = player.search(
        game,
        depth=2,
        alpha=float("-inf"),
        beta=4.0,
        player_to_max=0,
        next_player=0,
    )

    assert (score, move) == (5.0, "move-b")
    assert player.history_table["move-b"] == 4


def test_search_min_branch_returns_lowest_value_and_prunes() -> None:
    game = DummyGame(set())
    player = create_player(game, depth=2)
    score_by_move = {"move-a": 1.0, "move-b": 9.0}

    player._time_exceeded = lambda: False
    player.terminal = lambda tiles_info: False
    player.get_possible_moves = lambda tile, game: ["move-a", "move-b"]

    def fake_play(game: DummyGame, move: str) -> bool:
        game.last_move = move
        return True

    player.play_move_for_ai = fake_play
    player.star25 = lambda game, *args: score_by_move[game.last_move]
    player.undo_for_ai = lambda game: None

    score, move = player.search(
        game,
        depth=2,
        alpha=2.0,
        beta=float("inf"),
        player_to_max=0,
        next_player=1,
    )

    assert (score, move) == (1.0, "")
    assert player.history_table["move-a"] == 4


def test_event_prob_num_successors_terminal_and_apply_chance_event() -> None:
    game = DummyGame(set())
    player = create_player(game)
    tiles_info = SimpleNamespace(tiles_count={"CFFF": 2, "CRRF": 0})

    assert player.event_prob(game.game_data.graph, "CFFF", {"CFFF": 2}) == 1.0
    assert player.event_prob(game.game_data.graph, "CFFF", {}) == 0.0
    assert player.num_successors(tiles_info) == {"CFFF": 2}
    assert player.terminal(SimpleNamespace(tiles_count={"CFFF": 0})) is True
    assert player.terminal(SimpleNamespace(tiles_count={"CFFF": 1})) is False

    player.apply_chance_event(game, "CRRF")
    assert game.game_data.current_hand == "CRRF"


def test_n_probe_returns_eval_when_no_move_exists() -> None:
    game = DummyGame(set())
    player = create_player(game)
    player.get_possible_moves = lambda tile, game: []

    assert player.n_probe(game, -5.0, 5.0, 2, 0, 1) == 7.0


def test_n_probe_returns_beta_on_cutoff_and_restores_hand() -> None:
    game = DummyGame(set(), current_hand="CFFF")
    player = create_player(game)

    player._time_exceeded = lambda: False
    player.get_possible_moves = lambda tile, game: ["move-a", "move-b"]

    def fake_play(game: DummyGame, move: str) -> bool:
        game.last_move = move
        game.game_data.current_hand = "TEMP"
        return True

    player.play_move_for_ai = fake_play
    player.undo_for_ai = lambda game: None
    player.star25 = lambda game, *args: {"move-a": 10.0, "move-b": 3.0}[
        game.last_move
    ]

    assert player.n_probe(game, 0.0, 5.0, 2, 0, 1) == 5.0
    assert game.game_data.current_hand == "CFFF"


def test_star25_returns_weighted_value_and_restores_current_hand() -> None:
    game = DummyGame(set(), current_hand="START")
    player = create_player(game)

    player._time_exceeded = lambda: False
    player.terminal = lambda tiles_info: False
    player.num_successors = lambda tiles_info: {"A": 1, "B": 1}
    player.apply_chance_event = (
        lambda game, tile: setattr(game.game_data, "current_hand", tile)
    )
    player.n_probe = lambda *args, **kwargs: 0.0
    player.search = lambda game, *args: (
        3.0 if game.game_data.current_hand == "A" else 5.0,
        "",
    )

    assert player.star25(game, 2, -10.0, 10.0, 0, 1) == 4.0
    assert game.game_data.current_hand == "START"


def test_star25_returns_beta_when_search_phase_exceeds_bound() -> None:
    game = DummyGame(set(), current_hand="START")
    player = create_player(game)

    player._time_exceeded = lambda: False
    player.terminal = lambda tiles_info: False
    player.num_successors = lambda tiles_info: {"A": 1}
    player.apply_chance_event = (
        lambda game, tile: setattr(game.game_data, "current_hand", tile)
    )
    player.n_probe = lambda *args, **kwargs: 0.0
    player.search = lambda *args, **kwargs: (6.0, "")

    assert player.star25(game, 2, -10.0, 5.0, 0, 1) == 5.0


def test_star25_returns_alpha_when_search_phase_drops_below_bound() -> None:
    game = DummyGame(set(), current_hand="START")
    player = create_player(game)

    player._time_exceeded = lambda: False
    player.terminal = lambda tiles_info: False
    player.num_successors = lambda tiles_info: {"A": 1}
    player.apply_chance_event = (
        lambda game, tile: setattr(game.game_data, "current_hand", tile)
    )
    player.n_probe = lambda *args, **kwargs: 0.0
    player.search = lambda *args, **kwargs: (-10.0, "")

    assert player.star25(game, 2, -5.0, 100.0, 0, 1) == -5.0


def test_play_move_for_ai_and_undo_restore_previous_state() -> None:
    game = DummyGame({"CFFF/0N0/NW"}, meeples=1, current_hand="CFFF")
    player = create_player(game)

    assert player.play_move_for_ai(game, "CRRF/0N0") is False

    original_player = game.get_current_player()
    original_score = original_player.get_score_int()
    original_meeples = original_player.get_meeples()

    assert player.play_move_for_ai(game, "CFFF/0N0/NW") is True
    assert game.game_data.current_hand is None
    assert game.game_data.current_player_order_list == 1
    assert game.game_data.history.past_moves[-1].move_str == "CFFF/0N0/NW"
    assert original_player.get_score_int() == original_score + 5
    assert original_player.get_meeples() == original_meeples - 1

    player.undo_for_ai(game)

    assert game.game_data.current_player_order_list == 0
    assert game.game_data.current_hand is None
    assert original_player.get_score_int() == original_score
    assert original_player.get_meeples() == original_meeples
    assert game.game_data.board.removed_moves == ["0:CFFF/0N0/NW;"]
    assert game.game_data.board.scored_components == {"before"}
    assert game.game_data.graph.lands_components == {"before": [1]}
    assert game.game_data.graph.next_set_id == 3


def test_iterative_deepening_uses_previous_best_move_to_order_next_depth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created_solvers: list[SimpleNamespace] = []

    class FakeSolver:
        def __init__(
            self,
            game,
            start_time,
            max_time,
            depth,
            eval_name="",
            eval_fn=None,
            preferred_root_move=None,
            history_table=None,
        ) -> None:
            created_solvers.append(
                SimpleNamespace(
                    depth=depth,
                    preferred_root_move=preferred_root_move,
                    history_table=history_table,
                )
            )
            self.depth = depth

        def search(self, game, **kwargs):
            if self.depth == 1:
                return 1.0, "move-a"
            return 2.5, "move-b"

    monkeypatch.setattr(expectimax_module, "ExpectimaxPlayer", FakeSolver)

    player = IterativeDeepeningPlayer(
        DummyGame(set()),
        start_time=0.0,
        max_time=100.0,
        max_depth=2,
    )
    player._time_exceeded = lambda: False

    assert player.search(DummyGame(set()), -10.0, 10.0, 0, 0) == (
        2.5,
        "move-b",
    )
    assert player.last_completed_depth == 2
    assert player.history_table == {"move-a": 1, "move-b": 4}
    assert created_solvers[0].preferred_root_move == ""
    assert created_solvers[1].preferred_root_move == "move-a"


def test_iterative_deepening_keeps_last_complete_result_on_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeSolver:
        def __init__(
            self,
            game,
            start_time,
            max_time,
            depth,
            eval_name="",
            eval_fn=None,
            preferred_root_move=None,
            history_table=None,
        ) -> None:
            self.depth = depth

        def search(self, game, **kwargs):
            if self.depth == 1:
                return 1.0, "move-a"
            return 99.0, ""

    monkeypatch.setattr(expectimax_module, "ExpectimaxPlayer", FakeSolver)

    player = IterativeDeepeningPlayer(
        DummyGame(set()),
        start_time=0.0,
        max_time=100.0,
        max_depth=2,
    )
    timeout_states = iter([False, False, False, True])
    player._time_exceeded = lambda: next(timeout_states)

    assert player.search(DummyGame(set()), -10.0, 10.0, 0, 0) == (
        1.0,
        "move-a",
    )
    assert player.last_completed_depth == 1
