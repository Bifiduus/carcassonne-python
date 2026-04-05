from carcassonne.business_logic.ai_model import is_ai_player
from carcassonne.business_logic.score_manager import ScoreManager
from carcassonne.datas.deck import Deck


class UndoRedoManager:
    """Handle undo/redo by replaying the game from recorded move history."""

    def __init__(self, blitz_manager, deck_manager, game_data):
        """Initialise the manager with the shared game state and sub-managers.

        Args:
            blitz_manager: Handles blitz-mode timer and playability checks.
            deck_manager:  Provides deck shuffling for state reconstruction.
            game_data:     Centralises all mutable game state.

        Returns:
            None.
        """
        self.game_data = game_data
        self.blitz_manager = blitz_manager
        self.deck_manager = deck_manager

    def _can_time_travel(self) -> bool:
        """Return whether current state allows undo/redo operations.

        Returns:
            True if the current player is human and able to act,
            False otherwise.
        """
        # Blitz mode may lock the player if their timer has expired.
        if not self.blitz_manager._ensure_current_player_playable():
            return False
        # Only human players may trigger undo/redo; AI moves are automatic.
        return not self.game_data.get_current_player().is_ai_player()

    def _move_last_past_to_future(self):
        """Move one record from past history to future history.

        Returns:
            The MoveRecord that was transferred to the future stack.
        """
        last_played_record = self.game_data.history.pop_past()
        # Keep the record in future_moves so redo can replay it later.
        self.game_data.history.push_future(last_played_record)
        return last_played_record

    def _move_last_future_to_past(self):
        """Move one record from future history back to past history.

        Returns:
            The MoveRecord that was transferred back to the past stack.
        """
        last_undone_record = self.game_data.history.pop_future()
        # Reinstate the record in past_moves so the replay loop includes it.
        self.game_data.history.push_past(last_undone_record)
        return last_undone_record

    def _advance_deck_for_replayed_move(self, move_str: str) -> None:
        """Advance deck state so replay mirrors original draw order.

        Args:
            move_str: The recorded move string (e.g. "D/4/3/0").
        """
        tile_code = move_str.split("/")[0]
        # River tiles are identified by the "S" prefix in their code.
        if "S" in tile_code:
            self.game_data.deck.draw_river_tile()
        else:
            self.game_data.deck.draw()

    def _reset_players_state(self) -> None:
        """Reset score and meeple pool before replaying move history."""
        for player in self.game_data.players.values():
            player.get_score().set_points(0)
            player.meeples = 7  # Each player starts a game with 7 meeples.

    def _apply_end_game_score_if_needed(self) -> None:
        """Recompute end-game scoring when rebuilt state is terminal."""
        # Clear the flag to allow scoring even if already applied before.
        self.game_data._end_game_scored = False
        if (
            self.game_data.deck.is_empty()
            or not self.blitz_manager._has_playable_player()
        ):
            ScoreManager.score_end_of_game(
                self.game_data.graph,
                self.game_data.players,
            )
            self.game_data._end_game_scored = True

    def undo(self) -> None:
        """Undo the last human move and subsequent AI moves."""

        if not self._can_time_travel():
            return

        if not self.game_data.history.past_moves:
            return

        last_played_record = self._move_last_past_to_future()
        if is_ai_player(last_played_record):
            # The last move was an AI move, which means the human move that
            # triggered it also needs to be undone.  First strip all trailing
            # consecutive AI moves from the past stack.
            while self.game_data.history.past_moves and is_ai_player(
                self.game_data.history.past_moves[-1]
            ):
                self._move_last_past_to_future()

            # Then move the human move that preceded the AI sequence.
            if self.game_data.history.past_moves:
                self._move_last_past_to_future()

        # Full replay is needed: board/graph state is not reversible.
        self._rebuild_state_from_history()

    def redo(self) -> None:
        """Redo the last undone human move and subsequent AI moves."""

        if not self._can_time_travel():
            return

        if not self.game_data.history.future_moves:
            return

        # Restore the next undone move (always a human move at this point).
        self._move_last_future_to_past()
        # Also re-apply any consecutive AI moves that originally followed it.
        while self.game_data.history.future_moves and is_ai_player(
            self.game_data.history.future_moves[-1]
        ):
            self._move_last_future_to_past()

        self._rebuild_state_from_history()

    def _rebuild_state_from_history(self) -> None:
        """Rebuild game state from history to restore full consistency."""
        # Snapshot both stacks before reset wipes them.
        past_moves = list(self.game_data.history.past_moves)
        future_moves = list(self.game_data.history.future_moves)

        # Wipe board, graph, scores, and other runtime state.
        self.game_data.reset()

        # Restore the history stacks so undo/redo remain available afterwards.
        self.game_data.history.past_moves = list(past_moves)
        self.game_data.history.future_moves = list(future_moves)

        # Scores and meeple counts are recomputed during replay below.
        self._reset_players_state()

        # Re-create and re-shuffle the deck with the original seed so that the
        # draw order matches the one used during the original game.
        self.game_data.deck = Deck()
        self.deck_manager.shuffle_deck(
            self.game_data.shuffle_algo, self.game_data.seed
        )

        for move_record in past_moves:
            move_player = self.game_data.players.get(move_record.player_id)
            if move_player is None:
                continue

            # Replay the placement without re-recording it in history.
            self.game_data.board.add_tile_to_board(
                move_record.move_str,
                self.game_data.graph,
                self.game_data.tiles_info,
                self.game_data.history,
                self.game_data.players,
                self.game_data.players_order,
                move_player,
                record_history=False,
            )
            # Keep the deck pointer in sync with how many tiles were drawn.
            self._advance_deck_for_replayed_move(move_record.move_str)

        # The current player is determined by the position in the turn order,
        # which cycles through players_order with each played move.
        self.game_data.current_player_order_list = len(past_moves) % len(
            self.game_data.players_order
        )

        # Reapply end-game scoring if the rebuilt state is already terminal.
        self._apply_end_game_score_if_needed()

        # Advance past any AI players who cannot act at this point.
        self.blitz_manager._ensure_current_player_playable()
