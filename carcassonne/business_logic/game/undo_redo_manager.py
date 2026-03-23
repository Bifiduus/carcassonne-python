from carcassonne.business_logic.ai_model import is_ai_player
from carcassonne.datas.history import History


class UndoRedoManager:
    def __init__(self, game_data):
        self.game_data = game_data
        self.history: History = History()

    def undo(self) -> None:
        """Undo the last human move and subsequent AI moves."""

        if not self._ensure_current_player_playable():
            return

        if (
            self.game_data.rules_manager.current_player_is_human()
            and self.history.past_moves
        ):
            previous_play = self.history.pop_past()
            self.history.push_future(previous_play)
            while self.history.past_moves and is_ai_player(
                self.history.past_moves[-1]
            ):
                previous_play = self.history.pop_past()
                self.history.push_future(previous_play)

            self._rebuild_state_from_history()

    def redo(self) -> None:
        """Redo the last undone human move and subsequent AI moves."""

        if not self._ensure_current_player_playable():
            return

        if (
            self.game_data.current_player_is_human()
            and self.history.future_moves
        ):
            last_unplayed_move = self.history.pop_future()
            self.history.push_past(last_unplayed_move)
            while self.history.future_moves and is_ai_player(
                self.history.future_moves[-1]
            ):
                self.history.push_past(self.history.pop_future())

            self._rebuild_state_from_history()

    def _rebuild_state_from_history(self) -> None:
        """Rebuild full game state from past moves to keep data coherent."""
        past_moves = list(self.history.past_moves)

        self.game_data.reset()

        for player in self.game_data.players.values():
            player.get_score().set_points(0)
            player.meeples = 7

        self.game_data.shuffle_deck(
            self.game_data.shuffle_algo, self.game_data.seed)

        for record in past_moves:
            player = self.game_data.players.get(record.player_id)
            if player is None:
                continue

            self.game_data.board.add_tile_to_board(
                record.move_str,
                self.game_data.graph,
                self.game_data.tiles_info,
                self.history,
                self.game_data.players,
                self.game_data.players_order,
                player,
                record_history=False,
            )

        self.current_player_order_list = len(self.history.past_moves) % len(
            self.game_data.players_order
        )
        self._ensure_current_player_playable()

    def _ensure_current_player_playable(self) -> bool:
        if not self._is_blitz_enabled():
            return True
        if not self._advance_to_next_playable_player():
            return False

        current_player_id = self.get_current_player().get_id()
        if self.blitz_manager.active_player_id != current_player_id:
            self.blitz_manager.start_turn(current_player_id)
        return True
