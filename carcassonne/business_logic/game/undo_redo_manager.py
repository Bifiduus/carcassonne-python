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

    @staticmethod
    def _tile_code_from_move(move_str: str) -> str:
        """Return the tile code embedded in a move string.

        Args:
            move_str: A move string such as ``"CFFF/0N0"`` or
                ``"FSRS/m/1W0"``.

        Returns:
            The tile code, e.g. ``"CFFF"`` or ``"FSRS/m"``.
        """
        parts = move_str.split("/")
        if len(parts) >= 2 and len(parts[1]) == 1:
            return f"{parts[0]}/{parts[1]}"
        return parts[0]

    @staticmethod
    def _is_river_tile(tile_code: str) -> bool:
        """Return True when ``tile_code`` belongs to the river suit.

        Args:
            tile_code: Tile code as returned by ``_tile_code_from_move``,
                e.g. ``"FSRS/m"`` or ``"CFFF"``.

        Returns:
            True if the four-letter base code contains an 'S' (river) side.
        """
        return "S" in tile_code.split("/")[0]

    def _advance_deck_for_replayed_move(self, move_str: str) -> None:
        """Advance deck state so replay mirrors original draw order.

        Args:
            move_str: The recorded move string (e.g. "D/4/3/0").
        """
        tile_code = self._tile_code_from_move(move_str)
        if self._is_river_tile(tile_code):
            self.game_data.deck.draw_river_tile()
        else:
            self.game_data.deck.draw()

    def _reset_players_state(self) -> None:
        """Reset score and meeple pool before replaying move history."""
        for player in self.game_data.players.values():
            player.get_score().set_points(0)
            player.meeples = 7  # Each player starts a game with 7 meeples.

    def _apply_end_game_score_if_needed(self) -> None:
        """Recompute end-game scoring when rebuilt state is terminal.

        Note: relies on ``blitz_manager._has_playable_player()`` — a private
        method of BlitzManager.  If that class is ever refactored, this call
        site must be updated accordingly.
        """
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

        # Re-create and re-shuffle the deck with the original seed so that
        # the draw order matches the one used during the original game.
        self.game_data.deck = Deck()
        self.deck_manager.shuffle_deck(
            self.game_data.shuffle_algo, self.game_data.seed
        )

        self._replay_moves_onto_board(past_moves)
        self._restore_current_player(past_moves, future_moves)
        self._apply_end_game_score_if_needed()
        self.blitz_manager._ensure_current_player_playable()
        self._restore_hand_and_realign_deck(future_moves)

    def _replay_moves_onto_board(self, past_moves: list) -> None:
        """Replay every past move onto the board and advance the deck pointer.

        Args:
            past_moves: Ordered list of MoveRecord objects to replay.
        """
        for move_record in past_moves:
            move_player = self.game_data.players.get(move_record.player_id)
            if move_player is None:
                continue
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
            self._advance_deck_for_replayed_move(move_record.move_str)

    def _restore_current_player(
        self, past_moves: list, future_moves: list
    ) -> None:
        """Set current_player_order_list from history context.

        Using ``len(past_moves) % len(players_order)`` is wrong when
        ``players_order[0]`` is an AI (random shuffle at game start): it
        would point to the AI, causing ``_tick_once`` to auto-play and
        consume the tile that belongs to the human.  Reading the player id
        directly from ``future_moves`` avoids this entirely.

        Args:
            past_moves:   Moves already committed after rebuild.
            future_moves: Moves not yet replayed (undo stack).
        """
        if future_moves:
            next_player_id = future_moves[-1].player_id
            self.game_data.current_player_order_list = (
                self.game_data.players_order.index(next_player_id)
            )
        else:
            self.game_data.current_player_order_list = len(
                past_moves
            ) % len(self.game_data.players_order)

    def _restore_hand_and_realign_deck(self, future_moves: list) -> None:
        """Restore the player's in-hand tile and realign the deck.

        After a rebuild the human's drawn tile must remain in hand so that
        their next ``draw`` returns the correct tile without touching the
        deck.  AI moves that would follow are pre-positioned at the top of
        the appropriate tile list so their draws reproduce the original
        sequence.

        Args:
            future_moves: Moves not yet replayed, human move last.
        """
        if not future_moves:
            return
        # Restore the tile the human had in hand.
        self.game_data.current_hand = self._tile_code_from_move(
            future_moves[-1].move_str
        )
        # Align the deck for the AI moves that originally followed.
        # future_moves[:-1] are the AI moves to be replayed next.
        # Iterate in stored stack order so the earliest replayed AI move ends
        # up at draw-top (end for normal deck, front for river deck).
        for record in future_moves[:-1]:
            tile = self._tile_code_from_move(record.move_str)
            if self._is_river_tile(tile):
                lst = self.game_data.deck.river_tiles
                if tile in lst:
                    lst.insert(0, lst.pop(lst.index(tile)))
            else:
                lst = self.game_data.deck.tiles
                if tile in lst:
                    lst.append(lst.pop(lst.index(tile)))
