"""Widget that displays the list of players and their colour.

The view is intended to be placed in the top‑left corner of the game overlay.
It will be refreshed whenever the game state changes so that the user can see
which players are in the game, what colour they are using, and which one is
currently active.

Example usage from :class:`GameGUI`::

    self.players_view = PlayersView(self.game_data)
    overlay.add_overlay(self.players_view)

The view makes very few assumptions about the underlying game; it only
relies on the public ``game`` attribute exposed by :class:`GameDataGui`.  That
object is expected to expose a ``players`` dictionary keyed by player id and a
``get_current_player`` helper.  This keeps the widget decoupled enough that
it could be reused in other contexts or driven by a mock service in tests.
"""

from typing import Any
from gi.repository import Gtk
import gi

from carcassonne.i18n import gettext as _

gi.require_version("Gtk", "4.0")


class PlayersView(Gtk.Box):
    def __init__(self, game_data: Any) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.game_data = game_data

        # placement in the window
        self.set_halign(Gtk.Align.START)
        self.set_valign(Gtk.Align.START)
        self.set_margin_top(10)
        self.set_margin_start(10)

        # ---- title ----
        self.title = Gtk.Label(label=f"<b>{_('Players')}</b>")
        self.title.set_use_markup(True)
        self.append(self.title)

        # ---- area that will contain players ----
        self.players_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=4
        )
        self.append(self.players_box)

        self.refresh()

    # -------------------------------------------------

    def _format_time(self, seconds: float) -> str:
        """Format seconds as mm:ss."""
        total_seconds = max(0, int(seconds))
        minutes = total_seconds // 60
        secs = total_seconds % 60
        return f"{minutes}:{secs:02d}"

    def refresh(self) -> None:
        """Rebuild players list."""

        # remove previous players
        child = self.players_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.players_box.remove(child)
            child = next_child

        game = getattr(self.game_data, "game", None)
        if not game:
            return

        players = game.get_all_players()
        current = game.get_current_player()

        # Check if blitz mode is enabled
        is_blitz = game.get_game_configuration().get("blitz", False)

        for p in players:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

            name = p.get_username()
            score = p.get_score_int()
            color = p.get_color()
            meeple = p.get_meeples()
            player_id = p.get_id()

            label = Gtk.Label()
            label.set_use_markup(True)
            label.set_xalign(0)

            # Build the display text with blitz time if enabled
            base_text = f"{name} : {score} | {meeple}x"
            if is_blitz:
                remaining = game.get_player_remaining_time_seconds(
                    player_id) or 0
                time_str = self._format_time(remaining)
                base_text += f" | {time_str}"

            if p is current:
                label.set_markup(
                    f'<span foreground="{color}"><b>{base_text}</b></span>'
                )
                row.add_css_class("current-player")
            else:
                label.set_markup(
                    f'<span foreground="{color}">{base_text}</span>'
                )

            row.append(label)

            self.players_box.append(row)
