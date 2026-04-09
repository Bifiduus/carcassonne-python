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
        self.game_data.no_playable_tiles_remaining = False
        timed_out_now = self.blitz_manager.tick_blitz()
        if timed_out_now:
            return None
        if not self.blitz_manager._ensure_current_player_playable():
            return None

        if self.game_data.current_hand is not None:
            if self._is_tile_playable(self.game_data.current_hand):
                return self.game_data.current_hand
            self._put_tile_at_bottom(self.game_data.current_hand)
            self.game_data.current_hand = None

        attempts_left = self._remaining_draw_attempts()
        while attempts_left > 0:
            tile = self._draw_from_active_deck(silent=silent)
            if tile is None:
                return None

            if self._is_tile_playable(tile):
                self.game_data.current_hand = tile
                return tile

            self._put_tile_at_bottom(tile)
            attempts_left -= 1

        self._finalize_no_playable_tile_end_game(silent=silent)
        return None

    def _finalize_no_playable_tile_end_game(
        self, silent: bool = False
    ) -> None:
        """Record that no remaining tile is playable for the current state."""
        del silent
        self.game_data.current_hand = None
        self.game_data.no_playable_tiles_remaining = True

    def _draw_from_active_deck(self, silent: bool = False) -> str | None:
        if (
            self.river_manager.is_river_active()
            and not self.game_data.is_river_over()
        ):
            return self.game_data.deck.draw_river_tile(silent=silent)
        return self.game_data.deck.draw(silent=silent)

    def _remaining_draw_attempts(self) -> int:
        if (
            self.river_manager.is_river_active()
            and not self.game_data.is_river_over()
        ):
            if hasattr(self.game_data.deck, "len_river"):
                return self.game_data.deck.len_river()
            return len(getattr(self.game_data.deck, "river_tiles", []))

        if hasattr(self.game_data.deck, "len"):
            return self.game_data.deck.len()
        return len(getattr(self.game_data.deck, "tiles", []))

    @staticmethod
    def _move_prefix(tile: str) -> str:
        if "/" not in tile:
            return tile
        base, middle = tile.split("/", 1)
        return f"{base}/{middle}"

    @staticmethod
    def _is_river_tile(tile: str) -> bool:
        return "S" in tile.split("/")[0]

    def _put_tile_at_bottom(self, tile: str) -> None:
        if self._is_river_tile(tile):
            self.game_data.deck.river_tiles.append(tile)
            return
        self.game_data.deck.append(tile)

    def _is_tile_playable(self, tile: str) -> bool:
        """Return True if at least one legal move exists for ``tile``.

        When a lightweight test double does not expose full game state, this
        method returns True to preserve the previous draw behavior.
        """
        rules_manager = getattr(self.game_data, "rules_manager", None)
        graph = getattr(self.game_data, "graph", None)
        tiles_info = getattr(self.game_data, "tiles_info", None)
        get_player = getattr(self.game_data, "get_current_player", None)

        if not (
            rules_manager and graph and tiles_info and callable(get_player)
        ):
            return True

        current_player = get_player()
        if current_player is None:
            return True

        vertices = graph.get_vertices()
        direction_dict = getattr(tiles_info, "direction_dict", {})
        move_prefix = self._move_prefix(tile)
        player_id = current_player.get_id()

        for vertex_id, vertex in vertices.items():
            for direction in ["N", "E", "S", "W"]:
                side = direction_dict.get(direction)
                if side is None or not vertex.is_neighbor_free(side):
                    continue
                for rotation in range(4):
                    move = f"{move_prefix}/{vertex_id}{direction}{rotation}"
                    if rules_manager.check_move(
                        move,
                        graph,
                        self.river_manager,
                        current_player_id=player_id,
                    ):
                        return True
        return False

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
