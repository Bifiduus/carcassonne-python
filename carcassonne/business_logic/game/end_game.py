class EndGame():
    """Class to handle end game logic."""

    def __init__(self, game_data, blitz_manager, score_manager):
        self.game_data = game_data
        self.blitz_manager = blitz_manager
        self.score_manager = score_manager

    def end_game(self) -> bool:
        if self.game_data._end_game_scored:
            return True
        if (self.game_data.deck.is_empty() or
                not self.blitz_manager._has_playable_player()):
            self.score_manager.score_end_of_game(
                self.game_data.graph, self.game_data.players)
            self.game_data._end_game_scored = True
            return True
        else:
            return False
