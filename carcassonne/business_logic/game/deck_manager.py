from carcassonne.datas.seed import Seed


class DeckManager():
    """Class to manage the deck of the game, and be able to reset it when needed."""

    def __init__(self, game_data, blitz_manager, river_manager):
        self.game_data = game_data
        self.blitz_manager = blitz_manager
        self.river_manager = river_manager

    def draw_tile(self) -> str | None:
        """Draw a tile from the deck, checking blitz timeout and player playability."""
        timed_out_now = self.blitz_manager.tick_blitz()
        if timed_out_now:
            return None
        if not self.blitz_manager._ensure_current_player_playable():
            return None

        if self.game_data.current_hand is not None:
            return self.game_data.current_hand

        if self.river_manager.is_river_active() and not self.game_data.is_river_over():
            tile = self.game_data.deck.draw_river_tile()

        else :
            tile = self.game_data.deck.draw()

        if tile is None:
            return None
        self.game_data.current_hand = tile
        return tile

    def shuffle_deck(self, algo=None, seed=None) -> int:
        """Shuffle the deck using the specified algorithm and seed."""
        if algo is None:
            algo = self.game_data.shuffle_algo
        if seed is None:
            if self.game_data.default_seed is not None:
                seed = self.game_data.default_seed
            else:
                seed = Seed().seed
        if algo == "naive":
            self.game_data.deck.shuffle_naive(seed)
        else:
            self.game_data.deck.shuffle_fisher_yates(seed)
        self.game_data.seed = seed
        return seed
