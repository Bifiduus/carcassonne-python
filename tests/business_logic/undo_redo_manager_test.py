from carcassonne.business_logic.game.undo_redo_manager import UndoRedoManager
from carcassonne.datas.deck import Deck
from carcassonne.datas.history import History, MoveRecord


class DummyScore:
    def __init__(self) -> None:
        self.points = 0

    def set_points(self, points: int) -> None:
        self.points = points


class DummyPlayer:
    def __init__(self, is_ai: bool) -> None:
        self._is_ai = is_ai
        self._score = DummyScore()
        self.meeples = 7

    def is_ai_player(self) -> bool:
        return self._is_ai

    def get_score(self) -> DummyScore:
        return self._score


class DummyBoard:
    def __init__(self) -> None:
        self.played_moves: list[str] = []

    def add_tile_to_board(
        self,
        move,
        graph,
        tiles_info,
        history,
        players,
        players_order,
        current_player,
        record_history,
    ) -> None:
        self.played_moves.append(move)


class DummyDeckManager:
    def __init__(self) -> None:
        self.shuffle_calls: list[tuple[str, int]] = []

    def shuffle_deck(self, algo=None, seed=None) -> int:
        self.shuffle_calls.append((algo, seed))
        return seed


class DummyBlitzManager:
    def __init__(self) -> None:
        self.ensure_calls = 0

    def _ensure_current_player_playable(self) -> bool:
        self.ensure_calls += 1
        return True


class DummyGameData:
    def __init__(self) -> None:
        self.history = History()
        self.players = {0: DummyPlayer(False), 1: DummyPlayer(True)}
        self.players_order = [0, 1]
        self.current_player_order_list = 0
        self.shuffle_algo = "fisher-yates"
        self.seed = 42
        self.board = DummyBoard()
        self.graph = object()
        self.tiles_info = object()
        self.deck = Deck()

    def get_current_player(self) -> DummyPlayer:
        return self.players[0]

    def reset(self) -> None:
        # Mimic the production reset behavior that recreates history/board.
        self.history = History()
        self.board = DummyBoard()


def test_undo_then_redo_preserves_history_stacks() -> None:
    game_data = DummyGameData()
    blitz_manager = DummyBlitzManager()
    deck_manager = DummyDeckManager()
    manager = UndoRedoManager(blitz_manager, deck_manager, game_data)

    game_data.history.push_past(
        MoveRecord("CFFF/0N0", player_id=0, is_ai=False)
    )
    game_data.history.push_past(
        MoveRecord("FFRR/1N0", player_id=1, is_ai=True)
    )

    manager.undo()

    # Undo should keep the moved records in future even after state rebuild.
    assert len(game_data.history.past_moves) == 0
    assert len(game_data.history.future_moves) == 2

    manager.redo()

    # Redo restores the human+AI sequence from future to past.
    assert len(game_data.history.past_moves) == 2
    assert len(game_data.history.future_moves) == 0


def test_rebuild_reconstructs_deck_consumption_for_replayed_moves() -> None:
    game_data = DummyGameData()
    blitz_manager = DummyBlitzManager()
    deck_manager = DummyDeckManager()
    manager = UndoRedoManager(blitz_manager, deck_manager, game_data)

    game_data.history.push_past(
        MoveRecord("FSFS/0N0", player_id=0, is_ai=False)
    )
    game_data.history.push_past(
        MoveRecord("CFFF/0N0", player_id=0, is_ai=False)
    )

    initial_base_count = len(Deck().tiles)
    initial_river_count = len(Deck().river_tiles)

    manager._rebuild_state_from_history()

    assert game_data.board.played_moves == ["FSFS/0N0", "CFFF/0N0"]
    assert game_data.deck.len() == initial_base_count - 1
    assert game_data.deck.len_river() == initial_river_count - 1
