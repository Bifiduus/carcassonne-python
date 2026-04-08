import random

from carcassonne.interfaces.i_datas_factory import IDatasFactory


class DeckManager:
    """Manage the deck of the game, resetting it as needed."""

    def __init__(
        self,
        game_data,
        blitz_manager,
        river_manager,
        datas_factory: IDatasFactory,
    ):
        self.game_data = game_data
        self.blitz_manager = blitz_manager
        self.river_manager = river_manager
        self.datas_factory = datas_factory

    def draw_tile(self, silent: bool = False) -> str | None:
        """Draw a tile, checking blitz timeout and player playability."""
        timed_out_now = self.blitz_manager.tick_blitz()
        if timed_out_now:
            return None
        if not self.blitz_manager._ensure_current_player_playable():
            return None

        if self.game_data.current_hand is not None:
            return self.game_data.current_hand

        if (
            self.river_manager.is_river_active()
            and not self.game_data.is_river_over()
        ):
            tile = self.game_data.deck.draw_river_tile(silent=silent)

        else:
            tile = self.game_data.deck.draw(silent=silent)

        if tile is None:
            return None
        self.game_data.current_hand = tile
        return tile

    def resolve_seed(self, seed: int | None = None) -> int:
        """Resolve the seed used for deterministic game operations."""
        if seed is not None:
            return seed
        if self.game_data.default_seed is not None:
            return self.game_data.default_seed
        return self.datas_factory.create("Seed").seed

    @staticmethod
    def seed_runtime_rng(seed: int) -> None:
        """Seed the process-wide RNG used by player order and random AIs."""
        random.seed(seed)

    def shuffle_deck(self, algo=None, seed=None) -> int:
        """Shuffle the deck using the specified algorithm and seed."""
        if algo is None:
            algo = self.game_data.shuffle_algo
        seed = self.resolve_seed(seed)
        self.seed_runtime_rng(seed)
        if algo == "naive":
            self.game_data.deck.shuffle_naive(seed)
        else:
            self.game_data.deck.shuffle_fisher_yates(seed)
        self.game_data.seed = seed
        return seed
