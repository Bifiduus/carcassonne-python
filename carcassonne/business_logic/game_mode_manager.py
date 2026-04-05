"""Game mode coordination.

This module centralizes mode resolution so `Game` no longer embeds the
implementation details of each mode directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from carcassonne.business_logic.contest_manager import ContestManager

if TYPE_CHECKING:
    from carcassonne.business_logic.game import Game


class GameModeManager:
    """Resolve the active game mode and run mode-specific logic."""

    def __init__(self, blitz_manager, game: Game) -> None:
        self.game = game
        self.blitz_manager = blitz_manager
        self.contest_manager = ContestManager(game)

    def get_mode(self) -> str:
        """Return the current mode resolved from the existing config keys."""
        settings = self.game.get_game_configuration()
        contest_enabled = bool(settings.get("contest", False))
        contest_file = str(settings.get("contest_file", "") or "").strip()
        blitz_enabled = bool(settings.get("blitz", False))

        # Contest is explicitly enabled by CLI, with `contest_file` kept as a
        # compatibility fallback for existing GUI configuration.
        if contest_enabled or contest_file:
            return "contest"
        if blitz_enabled:
            return "blitz"
        return "default"

    def run_contest(self) -> str:
        """Execute the contest flow and return the move to print."""
        filename = str(self.game.get_game_configuration().get("contest_file", ""))
        return self.contest_manager.run(filename)

    def get_configured_blitz_minutes(self) -> int:
        raw_value = self.game.get_game_configuration().get("time", 30)
        try:
            minutes = int(raw_value)
        except (TypeError, ValueError):
            minutes = 30
        return minutes if minutes > 0 else 30

    def reset_for_current_state(self) -> None:
        mode = self.get_mode()
        self.blitz_manager.reset(
            player_ids=self.game.get_players_order(),
            enabled=mode == "blitz",
            minutes=self.get_configured_blitz_minutes(),
        )
        if mode == "blitz" and self.advance_to_next_playable_player():
            current_player_id = self.game.get_current_player().get_id()
            self.blitz_manager.start_turn(current_player_id)

    def has_playable_player(self) -> bool:
        players_order = self.game.get_players_order()
        if not players_order:
            return False
        if self.get_mode() != "blitz":
            return True
        for player_id in players_order:
            if not self.blitz_manager.is_player_timed_out(player_id):
                return True
        return False

    def advance_to_next_playable_player(self) -> bool:
        players_order = self.game.get_players_order()
        if not players_order:
            return False
        if self.get_mode() != "blitz":
            return True

        for _ in range(len(players_order)):
            player_id = players_order[
                self.game.game_data.current_player_order_list
            ]
            if not self.blitz_manager.is_player_timed_out(player_id):
                return True
            self.game.game_data.current_player_order_list = (
                self.game.game_data.current_player_order_list + 1
            ) % len(players_order)
        return False

    def skip_current_player(self) -> bool:
        """Skip current player and advance to the next playable player."""
        players_order = self.game.get_players_order()
        if not players_order:
            return False

        self.game.game_data.current_hand = None
        self.game.game_data.current_player_order_list = (
            self.game.game_data.current_player_order_list + 1
        ) % len(players_order)

        if not self.advance_to_next_playable_player():
            return False
        if self.get_mode() == "blitz":
            current_player_id = self.game.get_current_player().get_id()
            self.blitz_manager.start_turn(current_player_id)
        return True

    def ensure_current_player_playable(self) -> bool:
        if self.get_mode() != "blitz":
            return True
        if not self.advance_to_next_playable_player():
            return False

        current_player_id = self.game.get_current_player().get_id()
        if self.blitz_manager.active_player_id != current_player_id:
            self.blitz_manager.start_turn(current_player_id)
        return True

    def tick(self) -> bool:
        if self.get_mode() != "blitz":
            return False
        if not self.advance_to_next_playable_player():
            return False

        current_player_id = self.game.get_current_player().get_id()
        if self.blitz_manager.active_player_id != current_player_id:
            self.blitz_manager.start_turn(current_player_id)

        timed_out_now = self.blitz_manager.tick()
        if not timed_out_now:
            return False

        self.skip_current_player()
        return True

    def get_timeout_message(self) -> str:
        return self.blitz_manager.get_timeout_message()

    def get_current_player_remaining_time_seconds(self) -> float | None:
        if self.get_mode() != "blitz":
            return None
        self.tick()
        current_player_id = self.game.get_current_player().get_id()
        return self.blitz_manager.get_remaining_seconds(current_player_id)

    def get_player_remaining_time_seconds(
        self, player_id: int
    ) -> float | None:
        if self.get_mode() != "blitz":
            return None
        self.tick()
        if player_id not in self.game.game_data.players:
            return None
        return self.blitz_manager.get_remaining_seconds(player_id)

    def get_all_players_remaining_time_seconds(
        self,
    ) -> list[tuple[int, float]]:
        if self.get_mode() != "blitz":
            return []
        self.tick()
        return [
            (
                player_id,
                self.blitz_manager.get_remaining_seconds(player_id),
            )
            for player_id in self.game.get_players_order()
        ]
