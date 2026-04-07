"""Random AI player — selects a random legal move."""

from __future__ import annotations

import random as r
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from carcassonne.business_logic.game.game import Game


class RandomPlayer:

    # Example positions for meeple placement
    meeple_placement_list = ["NW", "N", "NE", "E", "SE", "S", "SW", "W", "C"]

    def get_possible_moves(self, tile, game: "Game") -> List[str]:
        """
        Generate all legal moves from the current game state.

        Args:
            graph: The game board graph
            rules_manager: Manager for game rules

        Returns:
            List of possible moves as strings
        """
        possible_moves = []

        # Try to place each available tile on each empty neighbor position
        vertices = game.game_data.graph.get_vertices()
        can_place_meeple = (
            game.game_data.get_current_player().get_meeples() > 0
        )
        meeple_indices = (
            range(-1, len(self.meeple_placement_list))
            if can_place_meeple
            else (-1,)
        )

        # Try to place the tile next to each existing vertex
        for vertex_id, vertex in vertices.items():
            # Try each direction (North, South, East, West)
            for direction in ["N", "S", "E", "W"]:
                # Check if this side is free
                if vertex.is_neighbor_free(
                    game.game_data.tiles_info.direction_dict.get(
                        direction, 0
                    )
                ):
                    # Try each rotation (0, 90, 180, 270 degrees)
                    for rotation in range(4):
                        # -1 means no meeple placement
                        for meeple in meeple_indices:
                            if meeple == -1:
                                move = (
                                    f"{tile}/{vertex_id}{direction}{rotation}"
                                )
                            else:
                                move = (
                                    f"{tile}/{vertex_id}{direction}{rotation}/"
                                    f"{self.meeple_placement_list[meeple]}"
                                )
                            # Verify the move is legal
                            id_player = (
                                game.game_data.get_current_player().get_id()
                            )
                            if game.game_data.rules_manager.check_move(
                                move,
                                game.game_data.graph,
                                game.river_manager,
                                current_player_id=id_player,
                            ):
                                possible_moves.append(move)
        return possible_moves

    def random_move(self, tile, game: "Game") -> str:
        """Select a random move from the list of possible moves."""
        possible_moves = self.get_possible_moves(tile, game)
        print(
            f"[DEBUG RandomPlayer] Possible moves for tile {tile}: {possible_moves}")
        selected_move = r.choice(possible_moves) if possible_moves else ""
        print(f"[DEBUG RandomPlayer] Selected move: {selected_move}")
        return selected_move
