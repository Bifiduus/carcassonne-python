"""Blitz time control management.

This module is intentionally self-contained so the game flow can delegate
all blitz timing responsibilities to a dedicated object.
"""

from __future__ import annotations

import time
from collections.abc import Iterable


class BlitzManager:
    """Track and update per-player clocks for blitz mode."""

    def __init__(self) -> None:
        self.enabled = False
        self.time_limit_seconds = 0.0
        self.remaining_time_seconds_by_player: dict[int, float] = {}
        self.active_player_id: int | None = None
        self.turn_started_at: float | None = None
        self.timed_out_player_ids: set[int] = set()
        self.timeout_message = ""

    def reset(
        self, player_ids: Iterable[int], enabled: bool, minutes: int = 30
    ) -> None:
        """Initialize clocks for a new game/session."""
        try:
            parsed_minutes = int(minutes)
        except (TypeError, ValueError):
            parsed_minutes = 30
        limit_minutes = parsed_minutes if parsed_minutes > 0 else 30
        self.enabled = bool(enabled)
        self.time_limit_seconds = float(limit_minutes * 60)
        self.remaining_time_seconds_by_player = {
            player_id: self.time_limit_seconds for player_id in player_ids
        }
        self.active_player_id = None
        self.turn_started_at = None
        self.timed_out_player_ids.clear()
        self.timeout_message = ""

    def start_turn(self, player_id: int) -> None:
        """Start or restart timing for the given player."""
        if not self.enabled or self.is_player_timed_out(player_id):
            return
        if player_id not in self.remaining_time_seconds_by_player:
            self.remaining_time_seconds_by_player[player_id] = (
                self.time_limit_seconds
            )
        self.active_player_id = player_id
        self.turn_started_at = time.monotonic()

    def consume_now(self) -> bool:
        """Consume elapsed time for the active player.

        Returns True if the active player timed out in this call.
        """
        if not self.enabled:
            return False
        if self.active_player_id is None or self.turn_started_at is None:
            return False
        if self.is_player_timed_out(self.active_player_id):
            self.active_player_id = None
            self.turn_started_at = None
            return False

        now = time.monotonic()
        elapsed = now - self.turn_started_at
        if elapsed <= 0:
            return False

        player_id = self.active_player_id
        current_remaining = self.remaining_time_seconds_by_player.get(
            player_id, self.time_limit_seconds
        )
        updated_remaining = current_remaining - elapsed
        self.remaining_time_seconds_by_player[player_id] = updated_remaining
        self.turn_started_at = now

        if updated_remaining <= 0:
            self.remaining_time_seconds_by_player[player_id] = 0.0
            self._register_timeout_loss(player_id)
            return True
        return False

    def tick(self) -> bool:
        """Alias used by periodic tick loops."""
        return self.consume_now()

    def end_turn(self, next_player_id: int) -> bool:
        """Close current turn accounting and start next player's timer."""
        timed_out_now = self.consume_now()
        if self.enabled and not self.is_player_timed_out(next_player_id):
            self.start_turn(next_player_id)
        return timed_out_now

    def has_timeout_loss(self) -> bool:
        return len(self.timed_out_player_ids) > 0

    def get_timeout_message(self) -> str:
        return self.timeout_message

    def is_player_timed_out(self, player_id: int) -> bool:
        return player_id in self.timed_out_player_ids

    def get_timed_out_players(self) -> list[int]:
        return sorted(self.timed_out_player_ids)

    def get_remaining_seconds(self, player_id: int) -> float:
        remaining = self.remaining_time_seconds_by_player.get(
            player_id, self.time_limit_seconds
        )
        return max(0.0, remaining)

    def _register_timeout_loss(self, player_id: int) -> None:
        if player_id in self.timed_out_player_ids:
            return

        self.timed_out_player_ids.add(player_id)
        self.active_player_id = None
        self.turn_started_at = None
        self.timeout_message = (
            f"Le temps du joueur {player_id} est écoulé: il ne pourra plus jouer dans cette partie."
        )
