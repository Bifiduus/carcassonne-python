from types import SimpleNamespace

import pytest

pytest.importorskip("gi")

from carcassonne.presentation.gui.players_view import PlayersView


class DummyPlayer:
    def __init__(self, player_id: int, name: str, color: str, score: int, meeples: int):
        self._id = player_id
        self._name = name
        self._color = color
        self._score = score
        self._meeples = meeples

    def get_id(self) -> int:
        return self._id

    def get_username(self) -> str:
        return self._name

    def get_color(self) -> str:
        return self._color

    def get_score_int(self) -> int:
        return self._score

    def get_meeples(self) -> int:
        return self._meeples


def _extract_row_texts(view: PlayersView) -> list[str]:
    texts = []
    row = view.players_box.get_first_child()
    while row:
        label = row.get_first_child()
        texts.append(label.get_text())
        row = row.get_next_sibling()
    return texts


def test_players_view_respects_turn_order() -> None:
    p1 = DummyPlayer(1, "Alice", "blue", 10, 5)
    p2 = DummyPlayer(2, "Bob", "red", 8, 6)
    p3 = DummyPlayer(3, "Cara", "green", 12, 4)

    game = SimpleNamespace(
        get_all_players=lambda: [p1, p2, p3],
        get_current_player=lambda: p2,
        get_players_order=lambda: [3, 1, 2],
        get_game_configuration=lambda: {"blitz": False},
    )
    game_data = SimpleNamespace(game=game)

    view = PlayersView(game_data)

    row_texts = _extract_row_texts(view)
    assert row_texts[0].startswith("Cara")
    assert row_texts[1].startswith("Alice")
    assert row_texts[2].startswith("Bob")


def test_players_view_falls_back_when_turn_order_missing() -> None:
    p1 = DummyPlayer(1, "Alice", "blue", 10, 5)
    p2 = DummyPlayer(2, "Bob", "red", 8, 6)

    game = SimpleNamespace(
        get_all_players=lambda: [p1, p2],
        get_current_player=lambda: p1,
        get_game_configuration=lambda: {"blitz": False},
    )
    game_data = SimpleNamespace(game=game)

    view = PlayersView(game_data)

    row_texts = _extract_row_texts(view)
    assert row_texts[0].startswith("Alice")
    assert row_texts[1].startswith("Bob")
