class DeckManager():
    """Class to manage the deck of the game, and be able to reset it when needed."""

    def __init__(self, game_data: GameData):
        self.game_data = game_data

    def draw_tile(self) -> str | None:
        timed_out_now = self.tick_blitz()
        if timed_out_now:
            return None
        if not self._ensure_current_player_playable():
            return None

        if self.current_hand is not None:
            return self.current_hand

        tile = self.deck.draw()
        if tile is None:
            return None
        self.current_hand = tile
        return tile

    def shuffle_deck(self, algo=None, seed=None):
        if algo is None:
            algo = self.shuffle_algo
        if seed is None:
            if self.default_seed is not None:
                seed = self.default_seed
            else:
                seed = Seed().seed
        if algo == "naive":
            self.deck.shuffle_naive(seed)
        else:
            self.deck.shuffle_fisher_yates(seed)
        self.seed = seed
        return seed
