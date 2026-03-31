from carcassonne.business_logic.ai_model import is_ai_player
from carcassonne.business_logic.score_manager import ScoreManager
from carcassonne.datas.deck import Deck


class UndoRedoManager:
    def __init__(self, blitz_manager, deck_manager, game_data):
        self.game_data = game_data
        self.blitz_manager = blitz_manager
        self.deck_manager = deck_manager

    def undo(self) -> None:
        """Undo the last human move and subsequent AI moves."""

        if not self.blitz_manager._ensure_current_player_playable():
            return

        current_player = self.game_data.get_current_player()
        if (
            not current_player.is_ai_player()
            and self.game_data.history.past_moves
        ):
            previous_play = self.game_data.history.pop_past()
            self.game_data.history.push_future(previous_play)
            if is_ai_player(previous_play):
                while self.game_data.history.past_moves and is_ai_player(
                    self.game_data.history.past_moves[-1]
                ):
                    previous_play = self.game_data.history.pop_past()
                    self.game_data.history.push_future(previous_play)

                if self.game_data.history.past_moves:
                    previous_play = self.game_data.history.pop_past()
                    self.game_data.history.push_future(previous_play)
            self._rebuild_state_from_history()

    def redo(self) -> None:
        """Redo the last undone human move and subsequent AI moves."""

        if not self.blitz_manager._ensure_current_player_playable():
            return

        current_player = self.game_data.get_current_player()
        if (
            not current_player.is_ai_player()
            and self.game_data.history.future_moves
        ):
            last_unplayed_move = self.game_data.history.pop_future()
            self.game_data.history.push_past(last_unplayed_move)
            while self.game_data.history.future_moves and is_ai_player(
                self.game_data.history.future_moves[-1]
            ):
                self.game_data.history.push_past(
                    self.game_data.history.pop_future()
                )

            self._rebuild_state_from_history()

    def _rebuild_state_from_history(self) -> None:
        """Rebuild full game state from past moves to keep data coherent."""
        past_moves = list(self.game_data.history.past_moves)
        future_moves = list(self.game_data.history.future_moves)

        self.game_data.reset()
        self.game_data.history.past_moves = list(past_moves)
        self.game_data.history.future_moves = list(future_moves)

        for player in self.game_data.players.values():
            player.get_score().set_points(0)
            player.meeples = 7

        self.game_data.deck = Deck()
        self.deck_manager.shuffle_deck(
            self.game_data.shuffle_algo, self.game_data.seed
        )

        for record in past_moves:
            player = self.game_data.players.get(record.player_id)
            if player is None:
                continue

            self.game_data.board.add_tile_to_board(
                record.move_str,
                self.game_data.graph,
                self.game_data.tiles_info,
                self.game_data.history,
                self.game_data.players,
                self.game_data.players_order,
                player,
                record_history=False,
            )
            # Advance the deck to match the tile that was drawn for this move
            tile_code = record.move_str.split("/")[0]
            if "S" in tile_code:
                self.game_data.deck.draw_river_tile()
            else:
                self.game_data.deck.draw()

        self.game_data.current_player_order_list = len(past_moves) % len(
            self.game_data.players_order
        )

        # Reset end-game scoring flag and reapply final scoring only if the
        # rebuilt position is terminal.
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

        self.blitz_manager._ensure_current_player_playable()
