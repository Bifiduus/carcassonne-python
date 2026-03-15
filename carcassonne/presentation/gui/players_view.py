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
import cairo
from gi.repository import Gtk, Gdk
import gi

gi.require_version("Gtk", "4.0")


class PlayersView(Gtk.Box):
    def __init__(self, game_data: Any) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.game_data = game_data

        # placement dans la fenêtre
        self.set_halign(Gtk.Align.START)
        self.set_valign(Gtk.Align.START)
        self.set_margin_top(10)
        self.set_margin_start(10)

        # ---- titre ----
        self.title = Gtk.Label(label="<b>Players</b>")
        self.title.set_use_markup(True)
        self.append(self.title)

        # ---- zone qui contiendra les joueurs ----
        self.players_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=4
        )
        self.append(self.players_box)

        self.refresh()

    # -------------------------------------------------

    def refresh(self) -> None:
        """Rebuild players list."""

        # supprimer anciens joueurs
        child = self.players_box.get_first_child()
        while child:
            next_child = child.get_next_sibling()
            self.players_box.remove(child)
            child = next_child

        game = getattr(self.game_data, "game", None)
        if not game:
            return

        players = list(game.players.values())
        current = game.get_current_player()

        for p in players:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)

            name = p.get_username()
            score = p.get_score_int()
            color = p.get_color()

            label = Gtk.Label()
            label.set_use_markup(True)
            label.set_xalign(0)

            if p is current:
                label.set_markup(
                    f'<span foreground="{color}"><b>{name} : {score}</b>'
                    "</span>"
                )
                row.add_css_class("current-player")
            else:
                label.set_markup(
                    f'<span foreground="{color}">{name} : {score}</span>'
                )

            row.append(label)

            self.players_box.append(row)
