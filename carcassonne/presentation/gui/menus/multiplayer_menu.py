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

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_margin_top(20)
        self.set_orientation(Gtk.Orientation.HORIZONTAL)
        self.set_spacing(20)

        # Left side has controls, right side shows players
        self.left_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.left_box.set_halign(Gtk.Align.FILL)
        self.left_box.set_valign(Gtk.Align.START)
        self.left_box.set_hexpand(True)

        self.players_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.players_box.set_halign(Gtk.Align.END)
        self.players_box.set_valign(Gtk.Align.START)
        self.players_box.set_margin_top(20)
        self.players_box.set_margin_end(20)
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
        self.left_box.append(title)

        self.append(self.left_box)
        self.append(self.players_box)

        # --- search servers  --------------------------------------------------
        server_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        btn_server = Gtk.Button(label="Server list")
        btn_server.add_css_class("back-buttons")
        btn_server.connect("clicked", self.on_server_list)
        btn_server.set_hexpand(False)

        server_box.set_halign(Gtk.Align.CENTER)
        server_box.append(btn_server)

        self.left_box.append(server_box)

        # --- show all players --------------------------------------------------
        # now always visible in right sidebar: no dedicated button needed
        self.refresh_players_view()

        # --- create server button ----------------------------------------
        create_server_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)

        btn_create_server = Gtk.Button(label="Create Server")
        btn_create_server.add_css_class("back-buttons")
        btn_create_server.connect("clicked", self.on_server_create)
        btn_create_server.set_hexpand(False)

        create_server_box.set_halign(Gtk.Align.CENTER)
        create_server_box.append(btn_create_server)

        self.left_box.append(create_server_box)
        self.entry_create = Gtk.Entry()
        self.entry_create.set_placeholder_text("(leave blank for random)")

        create_server_box.append(self.entry_create)
        self.left_box.append(create_server_box)

        # --- credentials section ----------------------------------------
        credentials_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)

        label_username = Gtk.Label(label="Username")
        self.entry_username = Gtk.Entry()
        self.entry_username.set_placeholder_text("Enter username")

        label_password = Gtk.Label(label="Password")
        self.entry_password = Gtk.Entry()
        self.entry_password.set_visibility(False)
        self.entry_password.set_placeholder_text("Enter password")

        btn_update = Gtk.Button(label="Update Credentials")
        btn_update.add_css_class("back-buttons")
        btn_update.connect("clicked", self.on_update_credentials)
        btn_update.set_hexpand(False)

        credentials_box.set_halign(Gtk.Align.CENTER)
        credentials_box.append(label_username)
        credentials_box.append(self.entry_username)
        credentials_box.append(label_password)
        credentials_box.append(self.entry_password)
        credentials_box.append(btn_update)

        self.left_box.append(credentials_box)

        # --- start / back buttons ----------------------------------------
        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        btn_back = Gtk.Button(label="Back")
        btn_back.add_css_class("back-buttons")
        btn_back.connect("clicked", self.on_back)
        btn_back.set_hexpand(False)

        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.append(btn_back)

        self.left_box.append(btn_box)

    # ------------------------------------------------------------------

    def on_update_credentials(self, button):
        """Update the user's credentials."""
        username = self.entry_username.get_text()
        password = self.entry_password.get_text()
        if username and password:
            self.gui.game_data.client.create_default_online_player(
                username, password, self.gui.game_data.server)
            # Maybe show a confirmation
            print(f"Credentials updated to {username}")
        else:
            print("Please enter both username and password")

    def on_server_list(self, button):
        """Show the server list."""
        servers = self.gui.game_data.client.list_available_servers()
        self.show_server_popup(servers)

    def show_server_popup(self, servers):
        """Affiche une popup avec la liste des serveurs."""

        popup = Gtk.Window(title="Available Servers")
        popup.set_modal(True)
        popup.set_transient_for(self.gui.window.window)
        popup.set_default_size(300, 400)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_margin_top(10)
        main_box.set_margin_bottom(10)
        main_box.set_margin_start(10)
        main_box.set_margin_end(10)

        listbox = Gtk.ListBox()

        for server in servers:
            row_box = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

            label = Gtk.Label(label=str(server), xalign=0)

            btn_join = Gtk.Button(label="Join")
            btn_join.connect("clicked", self.on_join_server, server, popup)

            row_box.append(label)
            row_box.append(btn_join)

            listbox.append(row_box)

        main_box.append(listbox)

        btn_close = Gtk.Button(label="Close")
        btn_close.connect("clicked", lambda b: popup.close())
        main_box.append(btn_close)

        popup.set_child(main_box)
        popup.present()

    def on_join_server(self, button, server, popup):
        """Rejoindre un serveur sélectionné."""
        print(f"Joining server: {server}")

        self.gui.game_data.client.join_server(server)

        popup.close()

    def on_show_all_players(self, button=None):
        """Refresh the player list in the right-side panel."""
        players = self.gui.game_data.client.repo.get_scoreboard()
        self.show_players_sidebar(players)

    def refresh_players_view(self):
        """Refresh players sidebar from repository without a button."""
        try:
            players = self.gui.game_data.client.repo.get_scoreboard()
        except Exception:
            players = []
        self.show_players_sidebar(players)

    def show_players_sidebar(self, players):
        """Display players in the right-side panel."""
        # Clear existing entries from listbox

        for player in players:
            row_box = Gtk.Box(
                orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            label = Gtk.Label(
                label=f"{player['username']} - Wins: {player['victories']}, Losses: {player['defeats']}",
                xalign=0,
            )
            row_box.append(label)
            self.players_listbox.append(row_box)

        self.players_box.set_visible(True)

    def on_server_create(self, button):
        """Create a server."""
        server_list = self.gui.game_data.server.server_start(
            self.entry_create.get_text())
        print(server_list)

    def on_back(self, button):
        """Validate configuration and start a new game."""
        # Validate contest file if contest mode is selected
        self.gui.window.stack.set_visible_child_name("menu")
