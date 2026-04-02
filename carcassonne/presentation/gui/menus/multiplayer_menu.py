from gi.repository import Gtk
import os

import gi

gi.require_version("Gtk", "4.0")


class MultiplayerMenu(Gtk.Box):
    """Simple form that lets the user pick a few configuration options.

    The view is shown when the player chooses *Singleplayer* (or the
    standalone *Options* button) from the main menu.  It doesn't attempt to
    replicate every setting that the command-line version exposes; at the
    moment we only wire up a random seed and a background image so that the
    information can actually be used by the rest of the GUI.  New fields can
    be added later as the project evolves.

    The view keeps a reference to the parent :class:`GameGUI` instance so that
    it can drive navigation and apply the selected options when the user
    presses the *Start* button.  A *Back* button simply returns the stack to
    the main menu.
    """

    def __init__(self, gui):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        self.gui = gui
        self.gui.window.stack.connect(
            "notify::visible-child", self._on_page_changed)

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_margin_top(20)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_spacing(20)

        # Create a grid layout: left spacer | center content | right players
        self.main_grid = Gtk.Grid()
        self.main_grid.set_column_spacing(20)
        self.main_grid.set_row_spacing(12)

        # Left scoreboard column
        self.scoreboard_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.scoreboard_box.set_halign(Gtk.Align.START)
        self.scoreboard_box.set_valign(Gtk.Align.START)
        self.scoreboard_box.set_size_request(280, -1)
        self.scoreboard_box.set_hexpand(False)
        self.scoreboard_box.add_css_class("scoreboard-sidebar")

        scoreboard_title = Gtk.Label(label="Scoreboard")
        scoreboard_title.add_css_class("section-title")
        self.scoreboard_box.append(scoreboard_title)

        self.scoreboard_listbox = Gtk.ListBox()
        self.scoreboard_box.append(self.scoreboard_listbox)

        # no hide button: always visible
        self.scoreboard_box.set_visible(True)

        # Center content column
        self.center_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.center_box.set_halign(Gtk.Align.CENTER)
        self.center_box.set_valign(Gtk.Align.START)
        self.center_box.set_hexpand(True)

        # Right players column
        self.players_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.players_box.set_halign(Gtk.Align.START)
        self.players_box.set_valign(Gtk.Align.START)
        self.players_box.set_size_request(280, -1)
        self.players_box.set_hexpand(False)
        self.players_box.add_css_class("players-sidebar")

        players_title = Gtk.Label(label="Players")
        players_title.add_css_class("section-title")
        self.players_box.append(players_title)

        self.players_listbox = Gtk.ListBox()
        self.players_box.append(self.players_listbox)

        # no hide button: always visible
        self.players_box.set_visible(True)

        title = Gtk.Label(label="Multiplayer")
        title.add_css_class("section-title")
        self.center_box.append(title)

        self.append(self.main_grid)
        self.main_grid.attach(self.scoreboard_box, 0, 0, 1, 1)
        self.main_grid.attach(self.center_box, 1, 0, 1, 1)
        self.main_grid.attach(self.players_box, 2, 0, 1, 1)

        # --- show all players --------------------------------------------------
        # now always visible in right sidebar: no dedicated button needed
        self.refresh_players_view()
        self.refresh_scoreboard_view()

        # --- server management menu button -----------------------------
        server_mgmt_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=5)
        btn_server_mgmt = Gtk.Button(label="Server Management")
        btn_server_mgmt.add_css_class("orange-buttons")
        btn_server_mgmt.connect("clicked", self.on_server_management)
        btn_server_mgmt.set_hexpand(False)

        server_mgmt_box.append(btn_server_mgmt)
        self.center_box.append(server_mgmt_box)

        # --- invitation management menu button -----------------------------
        invitation_mgmt_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=5)
        btn_invitation_mgmt = Gtk.Button(label="Party Invitations")
        btn_invitation_mgmt.add_css_class("orange-buttons")
        btn_invitation_mgmt.connect("clicked", self.on_invitation_management)
        btn_invitation_mgmt.set_hexpand(False)

        invitation_mgmt_box.append(btn_invitation_mgmt)
        self.center_box.append(invitation_mgmt_box)

        # --- start / back buttons ----------------------------------------
        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        btn_back = Gtk.Button(label="Back")
        btn_back.add_css_class("red-buttons")
        btn_back.connect("clicked", self.on_back)
        btn_back.set_hexpand(False)

        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.append(btn_back)

        self.center_box.append(btn_box)

    # ------------------------------------------------------------------

    def on_server_stop(self, button):
        """Stop the server."""
        self.gui.game_data.server.server_stop()

    def on_server_management(self, button):
        """Open the server management menu."""
        self.gui.window.stack.set_visible_child_name("server")

    def on_invitation_management(self, button):
        """Open the invitation management menu."""
        self.gui.window.stack.set_visible_child_name("invitation")

    def refresh_players_view(self):
        """Refresh players sidebar from server if running, else show empty."""
        try:
            players = self.gui.game_data.server.get_connected_players()
            self.show_connected_players_sidebar(players)
        except Exception as e:
            print(f"Error getting players: {e}")
            self.show_empty_sidebar()

    def _clear_players_listbox(self):
        """Remove all rows from the players listbox."""
        while True:
            row = self.players_listbox.get_first_child()
            if row is None:
                break
            self.players_listbox.remove(row)

    def show_connected_players_sidebar(self, players):
        """Display connected players in the right-side panel."""
        self._clear_players_listbox()

        for player in players:
            row_box = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            label = Gtk.Label(
                label=f"ID: {player['id']}, Name: {player['name']}, Status: {player['status']}",
                xalign=0,
            )
            row_box.append(label)
            self.players_listbox.append(row_box)

        self.players_box.set_visible(True)

    def show_empty_sidebar(self):
        """Clear the players sidebar."""
        self._clear_players_listbox()
        self.players_box.set_visible(True)

    def refresh_scoreboard_view(self):
        """Refresh scoreboard sidebar from server if running, else show empty."""
        try:
            if self.gui.game_data.server.is_server_running():
                players = self.gui.game_data.server.repo.get_scoreboard()
                self.show_scoreboard_sidebar(players)
            else:
                self.show_empty_scoreboard()
        except Exception as e:
            print(f"Error getting scoreboard: {e}")
            self.show_empty_scoreboard()

    def _clear_scoreboard_listbox(self):
        """Remove all rows from the scoreboard listbox."""
        while True:
            row = self.scoreboard_listbox.get_first_child()
            if row is None:
                break
            self.scoreboard_listbox.remove(row)

    def show_scoreboard_sidebar(self, players):
        """Display scoreboard in the left-side panel."""
        self._clear_scoreboard_listbox()

        for player in players:
            row_box = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            total_games = player['victories'] + player['defeats']
            label = Gtk.Label(
                label=f"{player['username']}: {player['victories']} wins, {player['defeats']} losses, {total_games} games",
                xalign=0,
            )
            row_box.append(label)
            self.scoreboard_listbox.append(row_box)

        self.scoreboard_box.set_visible(True)

    def show_empty_scoreboard(self):
        """Clear the scoreboard sidebar."""
        self._clear_scoreboard_listbox()
        self.scoreboard_box.set_visible(True)

    def on_back(self, button):
        """Validate configuration and start a new game."""
        # Validate contest file if contest mode is selected
        self.gui.window.stack.set_visible_child_name("menu")

    def show_message(self, title: str, message: str):
        """Show a message dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self.gui.window.window,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title
        )
        dialog.set_markup(message)
        dialog.connect("response", lambda d, r: d.destroy())
        dialog.present()

    def _on_page_changed(self, stack, _param):
        if stack.get_visible_child_name() == "multiplayer_menu":
            self.refresh_players_view()
            self.refresh_scoreboard_view()
