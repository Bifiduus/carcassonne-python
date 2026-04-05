from types import SimpleNamespace

from carcassonne.business_logic.ai.ai_manager import (
    AIModelManager,
    get_ai_move,
    initialize_ai,
    is_ai_player,
)
import carcassonne.business_logic.ai.ai_manager as ai_manager_module


class FakeExpectimaxPlayer:
    def __init__(self, depth: int, eval_name: str) -> None:
        self.depth = depth
        self.eval_name = eval_name
        self.nodes_explored = 99
        self.expectimax_calls = []
        self.evaluation_method = None

    def expectimax(self, **kwargs):
        self.expectimax_calls.append(kwargs)
        self.nodes_explored = 12
        return 3.5, "CFFF/0N0"

    def set_evaluation_method(self, name_or_fn) -> None:
        self.evaluation_method = name_or_fn


class FakeManager:
    def __init__(self, depth: int, eval_name: str) -> None:
        self.depth = depth
        self.eval_name = eval_name
        self.calls = []

    def choose_best_move(
        self,
        graph,
        tiles_info,
        rules_manager,
        ai_score,
        opponent_score,
    ):
        self.calls.append(
            (graph, tiles_info, rules_manager, ai_score, opponent_score)
        )
        return "CRRF/0N0"


def test_ai_model_manager_delegates_expectimax_calls(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "carcassonne.business_logic.ai.ai_manager.ExpectimaxPlayer",
        FakeExpectimaxPlayer,
    )
    manager = AIModelManager(depth=3, eval_name="baseline")

    best_move = manager.choose_best_move(
        graph="graph",
        tiles_info="tiles",
        rules_manager="rules",
        ai_score=7,
        opponent_score=5,
    )

    assert best_move == "CFFF/0N0"
    assert manager.player.nodes_explored == 12
    assert manager.player.expectimax_calls == [
        {
            "graph": "graph",
            "tiles_info": "tiles",
            "rules_manager": "rules",
            "depth": 3,
            "alpha": float("-inf"),
            "beta": float("inf"),
            "is_maximizing": True,
            "current_player_score": 7,
            "opponent_score": 5,
        }
    ]
    assert "AI explored 12 nodes" in capsys.readouterr().out


def test_ai_model_manager_updates_search_settings(monkeypatch) -> None:
    monkeypatch.setattr(
        "carcassonne.business_logic.ai.ai_manager.ExpectimaxPlayer",
        FakeExpectimaxPlayer,
    )
    manager = AIModelManager(depth=2, eval_name="baseline")

    manager.set_search_depth(6)
    manager.set_evaluation_method("short_term")

    assert manager.player.depth == 6
    assert manager.player.evaluation_method == "short_term"


def test_initialize_ai_and_get_ai_move_manage_global_manager(monkeypatch) -> None:
    monkeypatch.setattr(
        "carcassonne.business_logic.ai.ai_manager.AIModelManager",
        FakeManager,
    )
    ai_manager_module._ai_manager = None

    initialize_ai(depth=7, eval_name="disruption")
    assert isinstance(ai_manager_module._ai_manager, FakeManager)
    assert ai_manager_module._ai_manager.depth == 7
    assert ai_manager_module._ai_manager.eval_name == "disruption"

    ai_manager_module._ai_manager = None
    move = get_ai_move("graph", "tiles", "rules", 10, 3)

    assert move == "CRRF/0N0"
    assert ai_manager_module._ai_manager.calls == [
        ("graph", "tiles", "rules", 10, 3)
    ]


def test_is_ai_player_uses_optional_record_attribute() -> None:
    assert is_ai_player(SimpleNamespace(is_ai_move=True)) is True
    assert is_ai_player(SimpleNamespace()) is False
