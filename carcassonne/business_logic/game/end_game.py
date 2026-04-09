class EndGame:
    """Class to handle end game logic."""

    def __init__(self, game_data, blitz_manager, score_manager):
        self.game_data = game_data
        self.blitz_manager = blitz_manager
        self.score_manager = score_manager

    def end_game(self) -> bool:
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
        players = list(self.game_data.players.values())
        if not players:
            return []
        best_score = max(self._score_value(player) for player in players)
        return [
            player for player in players
            if self._score_value(player) == best_score
        ]

    def get_winner(self):
        winners = self.get_winners()
        if len(winners) != 1:
            return None
        return winners[0]

    def is_draw(self) -> bool:
        winners = self.get_winners()
        return len(winners) > 1
