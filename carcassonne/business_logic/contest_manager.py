"""Contest mode support."""

from __future__ import annotations

import contextlib
import io
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from carcassonne.business_logic.game import Game


class ContestManager:
    """Load a saved position and compute the move to print."""

    def __init__(self, game: "Game") -> None:
        self.game = game

    def run(self, filename: str) -> str:
        """Load the contest position and return the selected move."""
        if filename is None or filename.strip() == "":
            raise ValueError("contest mode requires a file")

        self._load_position(filename)
        return self._compute_move()

    def _load_position(self, filename: str) -> None:
        """Load the contest position with the existing game loader."""
        with contextlib.redirect_stdout(io.StringIO()):
            result = self.game.load_game_from_file(filename)

        if result != 0:
            raise ValueError(f"could not load contest file: {filename}")

    def _compute_move(self) -> str:
        """Let the built-in AI play one turn and read back the move."""
        current_player = self.game.get_current_player()
        original_is_ai = current_player.is_ai
        previous_history_length = len(self.game.history.past_moves)

        with contextlib.redirect_stdout(io.StringIO()):
            try:
                current_player.is_ai = True
                self.game.play_ai_turn()
            finally:
                current_player.is_ai = original_is_ai

        if len(self.game.history.past_moves) <= previous_history_length:
            raise ValueError("no legal move found for the current position")

        return self.game.history.past_moves[-1].move_str
