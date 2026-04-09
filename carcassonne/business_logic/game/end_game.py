class EndGame:
    """Class to handle end game logic."""

    def __init__(self, game_data, blitz_manager, score_manager):
        # All mutable game state (deck, players, board flags, …).
        self.game_data = game_data
        # Used to check whether any player can still legally act.
        self.blitz_manager = blitz_manager
        # Computes the final scores when the game ends.
        self.score_manager = score_manager

    def end_game(self) -> bool:
        """Check end-of-game conditions and apply final scoring if triggered.

        The game ends when:
        - The deck is empty, OR
        - No player has any time remaining (blitz mode), OR
        - All remaining tiles are proven unplayable.

        Final scoring is applied at most once (guarded by
        ``_end_game_scored``).

        Returns:
            True if the game has ended, False otherwise.
        """
        if self.game_data._end_game_scored:
            return True
        if (
            self.game_data.deck.is_empty()
            or not self.blitz_manager._has_playable_player()
            or getattr(self.game_data, "no_playable_tiles_remaining", False)
        ):
            self.score_manager.score_end_of_game(
                self.game_data.graph, self.game_data.players
            )
            self.game_data._end_game_scored = True
            self.game_data.no_playable_tiles_remaining = False
            return True
        else:
            return False

    @staticmethod
    def _score_value(player) -> int:
        """Extract an integer score from a player object regardless of its API.

        Tries ``get_score_int()``, then ``get_score().score``, then ``score``
        attribute, returning 0 if none are present.
        """
        if hasattr(player, "get_score_int"):
            return int(player.get_score_int())
        if hasattr(player, "get_score"):
            raw_score = player.get_score()
            if hasattr(raw_score, "score"):
                return int(raw_score.score)
            if isinstance(raw_score, (int, float)):
                return int(raw_score)
        if hasattr(player, "score"):
            raw_score = player.score
            if hasattr(raw_score, "score"):
                return int(raw_score.score)
            if isinstance(raw_score, (int, float)):
                return int(raw_score)
        return 0

    def get_winners(self) -> list:
        """Return all players sharing the highest score."""
        players = list(self.game_data.players.values())
        if not players:
            return []
        best_score = max(self._score_value(player) for player in players)
        return [
            player for player in players
            if self._score_value(player) == best_score
        ]

    def get_winner(self):
        """Return the sole winner, or None if there is a draw."""
        winners = self.get_winners()
        if len(winners) != 1:
            return None
        return winners[0]

    def is_draw(self) -> bool:
        """Return True when two or more players share the highest score."""
        winners = self.get_winners()
        return len(winners) > 1
