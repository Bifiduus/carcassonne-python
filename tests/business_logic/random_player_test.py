from types import SimpleNamespace

from carcassonne.business_logic.ai.random_player import RandomPlayer


class DummyVertex:
    def __init__(self, free_directions: set[int]) -> None:
        self.free_directions = free_directions

    def is_neighbor_free(self, direction: int) -> bool:
        return direction in self.free_directions


class DummyGraph:
    def get_vertices(self) -> dict[int, DummyVertex]:
        return {0: DummyVertex({0})}


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


class DummyPlayer:
    def __init__(self, player_id: int, meeples: int) -> None:
        self.player_id = player_id
        self.meeples = meeples

    def get_meeples(self) -> int:
        return self.meeples

    def get_id(self) -> int:
        return self.player_id


class DummyGameData:
    def __init__(self, allowed_moves: set[str], meeples: int) -> None:
        self.graph = DummyGraph()
        self.tiles_info = SimpleNamespace(direction_dict={"N": 0})
        self.rules_manager = DummyRulesManager(allowed_moves)
        self._current_player = DummyPlayer(0, meeples)

    def get_current_player(self) -> DummyPlayer:
        return self._current_player


class DummyGame:
    def __init__(self, allowed_moves: set[str], meeples: int) -> None:
        self.game_data = DummyGameData(allowed_moves, meeples)
        self.river_manager = object()


def test_get_possible_moves_without_meeples_only_considers_tile_placement() -> None:
    game = DummyGame({"CFFF/0N0"}, meeples=0)
    player = RandomPlayer()

    moves = player.get_possible_moves("CFFF", game)

    assert moves == ["CFFF/0N0"]
    assert all("/" not in move.removeprefix("CFFF/0N0") for move in moves)


def test_get_possible_moves_with_meeples_keeps_legal_meeple_moves() -> None:
    game = DummyGame({"CFFF/0N0/NW"}, meeples=1)
    player = RandomPlayer()

    moves = player.get_possible_moves("CFFF", game)

    assert moves == ["CFFF/0N0/NW"]
    assert game.game_data.rules_manager.checked_moves


def test_random_move_returns_empty_string_when_no_move_is_available() -> None:
    game = DummyGame(set(), meeples=1)
    player = RandomPlayer()

    assert player.random_move("CFFF", game) == ""
