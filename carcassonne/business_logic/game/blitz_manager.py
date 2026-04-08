"""Blitz time control management.

This module is intentionally self-contained so the game flow can delegate
all blitz timing responsibilities to a dedicated object.
"""

from __future__ import annotations

import time
from collections.abc import Iterable


class BlitzManager:
    """Track and update per-player clocks for blitz mode."""

    def __init__(self, game_data) -> None:
        self.game_data = game_data
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
            f"Player {player_id} ran out of time:"
            " they can no longer play in this game."
        )

    def _configured_blitz_minutes(self) -> int:
        settings = self.game_data.get_game_configuration()
        raw_value = settings.get("time", 30)
        try:
            minutes = int(raw_value)
        except (TypeError, ValueError):
            minutes = 30
        return minutes if minutes > 0 else 30

    def _is_blitz_enabled(self) -> bool:
        return bool(
            self.game_data.get_game_configuration().get("blitz", False)
        )

    def _initialize_blitz_state(self) -> None:
        self.reset(
            player_ids=self.game_data.players_order,
            enabled=self._is_blitz_enabled(),
            minutes=self._configured_blitz_minutes(),
        )
        condition = self._advance_to_next_playable_player()
        if self._is_blitz_enabled() and condition:
            self.start_turn(self.game_data.get_current_player().get_id())

    def _has_playable_player(self) -> bool:
        for player_id in self.game_data.players_order:
            if not self.is_player_timed_out(player_id):
                return True
        return False

    def _advance_to_next_playable_player(self) -> bool:
        if not self.game_data.players_order:
            return False

        for _ in range(len(self.game_data.players_order)):
            player_id = self.game_data.players_order[
                self.game_data.current_player_order_list
            ]
            if not self.is_player_timed_out(player_id):
                return True
            self.game_data.current_player_order_list = (
                self.game_data.current_player_order_list + 1
            ) % len(self.game_data.players_order)
        return False

    def skip_current_player(self) -> bool:
        """Skip current player and advance to the next playable player."""
        if not self.game_data.players_order:
            return False

        self.game_data.current_hand = None
        self.game_data.current_player_order_list = (
            self.game_data.current_player_order_list + 1
        ) % len(self.game_data.players_order)

        if not self._advance_to_next_playable_player():
            return False
        if self._is_blitz_enabled():
            self.start_turn(self.game_data.get_current_player().get_id())
        return True

    def tick_blitz(self) -> bool:
        if not self._is_blitz_enabled():
            return False
        if not self._advance_to_next_playable_player():
            return False

        current_player_id = self.game_data.get_current_player().get_id()
        if self.active_player_id != current_player_id:
            self.start_turn(current_player_id)

        timed_out_now = self.tick()
        if not timed_out_now:
            return False

        self.skip_current_player()
        return True

    def get_current_player_remaining_time_seconds(self) -> float | None:
        if not self._is_blitz_enabled():
            return None
        self.tick_blitz()
        current_player_id = self.game_data.get_current_player().get_id()
        return self.get_remaining_seconds(current_player_id)

    def get_player_remaining_time_seconds(
        self, player_id: int
    ) -> float | None:
        if not self._is_blitz_enabled():
            return None
        self.tick_blitz()
        if player_id not in self.game_data.players:
            return None
        return self.get_remaining_seconds(player_id)

    def get_all_players_remaining_time_seconds(
        self,
    ) -> list[tuple[int, float]]:
        if not self._is_blitz_enabled():
            return []
        self.tick_blitz()
        return [
            (
                player_id,
                self.get_remaining_seconds(player_id),
            )
            for player_id in self.game_data.players_order
        ]

    def _ensure_current_player_playable(self) -> bool:
        if not self._is_blitz_enabled():
            return True
        if not self._advance_to_next_playable_player():
            return False

        current_player_id = self.game_data.get_current_player().get_id()
        if self.active_player_id != current_player_id:
            self.start_turn(current_player_id)
        return True
