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

        title = Gtk.Label(label="Multiplayer")
        title.add_css_class("section-title")
        self.append(title)

        # --- search servers  --------------------------------------------------
        server_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        btn_server = Gtk.Button(label="Server list")
        btn_server.add_css_class("back-buttons")
        btn_server.connect("clicked", self.on_server_list)
        btn_server.set_hexpand(False)

        server_box.set_halign(Gtk.Align.CENTER)
        server_box.append(btn_server)

        self.append(server_box)

        # --- create server button ----------------------------------------
        create_server_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)

        btn_create_server = Gtk.Button(label="Create Server")
        btn_create_server.add_css_class("back-buttons")
        btn_create_server.connect("clicked", self.on_server_create)
        btn_create_server.set_hexpand(False)

        create_server_box.set_halign(Gtk.Align.CENTER)
        create_server_box.append(btn_create_server)

        self.append(create_server_box)
        self.entry_create = Gtk.Entry()
        self.entry_create.set_placeholder_text("(leave blank for random)")

        create_server_box.append(self.entry_create)
        self.append(create_server_box)

        # --- start / back buttons ----------------------------------------
        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        btn_back = Gtk.Button(label="Back")
        btn_back.add_css_class("back-buttons")
        btn_back.connect("clicked", self.on_back)
        btn_back.set_hexpand(False)

        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.append(btn_back)

        self.append(btn_box)

    # ------------------------------------------------------------------

    def on_server_list(self, button):
        """Show the server list."""
        servers = self.gui.game_data.server.list_available_servers()
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

        self.gui.game_data.server.join_server(server)

        popup.close()

    def on_server_create(self, button):
        """Create a server."""
        server_list = self.gui.game_data.server.server_start(
            self.entry_create.get_text())
        print(server_list)

    def on_back(self, button):
        """Validate configuration and start a new game."""
        # Validate contest file if contest mode is selected
        self.gui.window.stack.set_visible_child_name("menu")
