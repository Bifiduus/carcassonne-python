class EndGame():
    """Class to handle end game logic."""

    def __init__(self, game_data):
        self.game_data = game_data

    def end_game(self) -> bool:
        if self._end_game_scored:
            return True
        if self.deck.is_empty() or not self._has_playable_player():
            self.score_manager.score_end_of_game(self.graph, self.players)
            self._end_game_scored = True
            return True
        else:
            return False
