from gi.repository import Gtk, GLib

import gi

from carcassonne.presentation.interfaces.i_client_service import IClientService
from carcassonne.presentation.interfaces.i_server_service import IServerService

gi.require_version("Gtk", "4.0")


class ServerMenu(Gtk.Box):
    """Menu for managing server operations.

    This menu provides controls for server management including
    starting/stopping the server, viewing server status, managing
    connected players, and accessing server statistics.

    Follows 3-tier architecture by depending on IClientService and
    IServerService interfaces.
    """

    def __init__(
        self,
        gui,
        client_service: IClientService = None,
        server_service: IServerService = None,
    ):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        self.gui = gui
        # Use interfaces for services (3-tier architecture)
        self.client_service = client_service or (
            gui.game_data.client if gui.game_data else None)
        self.server_service = server_service or (
            gui.game_data.server if gui.game_data else None)
        self.current_port = "N/A"
        self._popup_pending = False

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.CENTER)
        self.set_margin_top(20)
        self.set_orientation(Gtk.Orientation.VERTICAL)
        self.set_spacing(20)

        # Main content box
        self.main_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.main_box.set_halign(Gtk.Align.CENTER)
        self.main_box.set_valign(Gtk.Align.START)
        self.main_box.set_hexpand(True)

        title = Gtk.Label(label="Server Management")
        title.add_css_class("section-title")
        self.main_box.append(title)

        self.append(self.main_box)

        # --- search servers ------------------------------------------------
        server_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        btn_server = Gtk.Button(label="Server list")
        btn_server.add_css_class("orange-buttons")
        btn_server.connect("clicked", self.on_server_list)
        btn_server.set_hexpand(False)

        server_box.set_halign(Gtk.Align.CENTER)
        server_box.append(btn_server)

        self.main_box.append(server_box)

        # --- Server Control Section ----------------------------------------
        server_control_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)
        server_control_box.set_halign(Gtk.Align.CENTER)

        server_control_title = Gtk.Label(label="Server Control")
        server_control_title.add_css_class("section-title")
        server_control_title.set_halign(Gtk.Align.CENTER)
        server_control_box.append(server_control_title)

        # Port input
        port_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        port_box.set_halign(Gtk.Align.CENTER)
        port_label = Gtk.Label(label="Port:")
        self.entry_port = Gtk.Entry()
        self.entry_port.set_placeholder_text("12345")
        self.entry_port.set_text("12345")
        port_box.append(port_label)
        port_box.append(self.entry_port)
        server_control_box.append(port_box)

        # Control buttons
        buttons_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        buttons_box.set_halign(Gtk.Align.CENTER)

        btn_start_server = Gtk.Button(label="Start Server")
        btn_start_server.add_css_class("orange-buttons")
        btn_start_server.connect("clicked", self.on_start_server)
        buttons_box.append(btn_start_server)

        btn_stop_server = Gtk.Button(label="Stop Server")
        btn_stop_server.add_css_class("orange-buttons")
        btn_stop_server.connect("clicked", self.on_stop_server)
        buttons_box.append(btn_stop_server)

        server_control_box.append(buttons_box)

        self.main_box.append(server_control_box)

        # --- Server Information Section -----------------------------------
        info_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)

        info_title = Gtk.Label(label="Server Information")
        info_title.add_css_class("section-title")
        info_box.append(info_title)

        # Status button
        btn_status = Gtk.Button(label="Server Status")
        btn_status.add_css_class("orange-buttons")
        btn_status.connect("clicked", self.on_server_status)
        info_box.append(btn_status)

        # Players button
        btn_players = Gtk.Button(label="Connected Players")
        btn_players.add_css_class("orange-buttons")
        btn_players.connect("clicked", self.on_show_players)
        info_box.append(btn_players)

        # Scoreboard button
        btn_scoreboard = Gtk.Button(label="Scoreboard")
        btn_scoreboard.add_css_class("orange-buttons")
        btn_scoreboard.connect("clicked", self.on_show_scoreboard)
        info_box.append(btn_scoreboard)

        self.main_box.append(info_box)

        # --- Connection Management Section ---------------------------------
        connection_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)

        connection_title = Gtk.Label(label="Connection Management")
        connection_title.add_css_class("section-title")
        connection_box.append(connection_title)

        # Connection buttons
        connection_buttons_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        connection_buttons_box.set_halign(Gtk.Align.CENTER)

        # Disconnect button (only shown if connected)
        self.btn_disconnect = Gtk.Button(label="Disconnect from Server")
        self.btn_disconnect.add_css_class("orange-buttons")
        self.btn_disconnect.connect("clicked", self.on_disconnect_from_server)
        self.btn_disconnect.set_visible(False)  # Hidden by default
        connection_buttons_box.append(self.btn_disconnect)

        # Ping button (only shown if connected)
        self.btn_ping = Gtk.Button(label="Ping Server")
        self.btn_ping.add_css_class("orange-buttons")
        self.btn_ping.connect("clicked", self.on_ping_server)
        self.btn_ping.set_visible(False)  # Hidden by default
        connection_buttons_box.append(self.btn_ping)

        # Stop local server button (only shown if server is running)
        self.btn_stop_local_server = Gtk.Button(label="Stop Local Server")
        self.btn_stop_local_server.add_css_class("orange-buttons")
        self.btn_stop_local_server.connect(
            "clicked", self.on_stop_local_server)
        self.btn_stop_local_server.set_visible(False)  # Hidden by default
        connection_buttons_box.append(self.btn_stop_local_server)

        connection_box.append(connection_buttons_box)

        # Update button visibility based on current state
        self.update_connection_buttons()

        self.main_box.append(connection_box)

        # --- Back Button -------------------------------------------------

        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        btn_back = Gtk.Button(label="Back to Multiplayer")
        btn_back.add_css_class("red-buttons")
        btn_back.connect("clicked", self.on_back)
        btn_back.set_hexpand(False)

        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.append(btn_back)

        self.main_box.append(btn_box)

    # ------------------------------------------------------------------

    def on_server_list(self, button):
        """Show the server list."""
        servers = self.client_service.list_available_servers()
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

            label = Gtk.Label(label=f"{server}:{servers[server]}", xalign=0)

            btn_join = Gtk.Button(label="Join")
            btn_join.connect("clicked", self.on_join_server, server, popup)

            row_box.append(label)
            row_box.append(btn_join)

            listbox.append(row_box)

        main_box.append(listbox)

        btn_close = Gtk.Button(label="Close")
        btn_close.connect("clicked", lambda b: popup.destroy())
        main_box.append(btn_close)

        popup.set_child(main_box)
        popup.present()

    def on_join_server(self, button, server, popup):
        """Rejoindre un serveur sélectionné."""
        try:
            print(f"Joining server: {server}")
            result = self.client_service.join_server(server)
            if result:
                # Ferme la popup de manière sécurisée
                GLib.idle_add(popup.destroy)
                self.update_connection_buttons()
            else:
                self.show_message("Error", "Failed to join server")
            # Response will arrive via visit_server_message() from server
        except Exception as e:
            print(f"Error joining server: {e}")
            self.show_message("Error", f"Error joining server: {e}")

    def on_start_server(self, button):
        """Start the server on the specified port."""
        port = self.entry_port.get_text() or "12345"
        try:
            self.server_service.server_start(port)
            self.current_port = port
            print(f"Server started successfully on port {port}")
            # Show success message
            self.show_message("Success", f"Server started on port {port}")
            self.update_connection_buttons()
        except Exception as e:
            print(f"Error starting server: {e}")
            self.show_message("Error", f"Error starting server: {e}")

    def on_stop_server(self, button):
        """Stop the running server."""
        try:
            self.server_service.server_stop()
            print("Server stopped")
            self.show_message("Success", "Server stopped successfully")
            self.update_connection_buttons()
        except Exception as e:
            print(f"Error stopping server: {e}")
            self.show_message("Error", f"Error stopping server: {e}")

    def on_server_status(self, button):
        """Show server status information."""
        try:
            is_running = self.server_service.is_server_running()

            connected_clients = len(
                self.server_service.connected_clients)
            active_games = self.server_service.number_current_games()

            status_text = f"Server Running: {is_running}\n"
            status_text += f"Port: {self.current_port}\n"
            status_text += f"Connected Clients: {connected_clients}\n"
            status_text += f"Active Games: {active_games}"

            self.show_message("Server Status", status_text)
        except Exception as e:
            print(f"Error getting server status: {e}")
            self.show_message("Error", f"Error getting server status: {e}")

    def on_show_players(self, button):
        """Show list of connected players."""
        try:
            players = self.server_service.get_connected_players()

            if players:
                players_text = "\n".join(
                    [
                        (
                            f"ID: {p['id']}, Name: {p['name']}, "
                            f"Status: {p['status']}"
                        )
                        for p in players
                    ]
                )
            else:
                players_text = "No players connected"

            self.show_message("Connected Players", players_text)
        except Exception as e:
            print(f"Error getting players: {e}")
            self.show_message("Error", f"Error getting players: {e}")

    def on_show_scoreboard(self, button):
        """Show server scoreboard."""
        try:
            scoreboard = self.server_service.repo.get_scoreboard()
            connected_players = self.server_service.get_connected_players()
            connected_usernames = {p['name'] for p in connected_players}

            if scoreboard:
                # Filter scoreboard to only connected players
                filtered_scoreboard = [
                    p
                    for p in scoreboard
                    if p['username'] in connected_usernames
                ]
                if filtered_scoreboard:
                    scoreboard_text = "\n".join(
                        [
                            (
                                f"{p['username']}: {p['victories']} wins, "
                                f"{p['defeats']} losses, "
                                f"{p['victories'] + p['defeats']} games played"
                            )
                            for p in filtered_scoreboard
                        ]
                    )
                else:
                    scoreboard_text = (
                        "No connected players with scoreboard data"
                    )
            else:
                scoreboard_text = "No scoreboard data available"

            self.show_message("Server Scoreboard", scoreboard_text)
        except Exception as e:
            print(f"Error getting scoreboard: {e}")
            self.show_message("Error", f"Error getting scoreboard: {e}")

    def on_back(self, button):
        """Return to the multiplayer menu."""
        self.gui.window.stack.set_visible_child_name("multiplayer_menu")

    def update_connection_buttons(self):
        """Update connection-button visibility from current state."""
        try:
            # Check if client is connected to a server
            is_connected = self.client_service.connected_to_a_server()
            self.btn_disconnect.set_visible(is_connected)
            self.btn_ping.set_visible(is_connected)

            # Check if local server is running
            server_running = self.server_service.is_server_running()
            self.btn_stop_local_server.set_visible(server_running)
        except Exception as e:
            print(f"Error updating connection buttons: {e}")
            self.btn_disconnect.set_visible(False)
            self.btn_ping.set_visible(False)
            self.btn_stop_local_server.set_visible(False)

    def on_disconnect_from_server(self, button):
        """Disconnect from the current server."""
        try:
            result = self.client_service.disconnect()
            if not result:
                self.show_message("Error", "Failed to disconnect")
            else:
                self.update_connection_buttons()
            # Response will arrive via visit_server_message() from server
        except Exception as e:
            print(f"Error disconnecting from server: {e}")
            self.show_message("Error", f"Error disconnecting from server: {e}")

    def on_stop_local_server(self, button):
        """Stop the local server."""
        try:
            self.server_service.server_stop()
            print("Local server stopped")
            self.show_message("Success", "Local server stopped successfully")
            self.update_connection_buttons()
        except Exception as e:
            print(f"Error stopping local server: {e}")
            self.show_message("Error", f"Error stopping local server: {e}")

    def on_ping_server(self, button):
        """Ping the connected server."""
        try:
            result = self.client_service.send_to_server("ping")
            if not result:
                self.show_message("Error", "Failed to send ping request")
            # Response will arrive via visit_server_message() from server
        except Exception as e:
            print(f"Error pinging server: {e}")
            self.show_message("Error", f"Error pinging server: {e}")

    def show_message(self, title: str, message):
        """Show a message dialog (GTK4 compatible)."""
        if isinstance(message, bool):
            message = "Success" if message else "Failure"
        elif message is None:
            message = "No response received"
        else:
            message = str(message)

        def _show_dialog():
            try:
                parent_window = None
                if (hasattr(self, 'gui') and self.gui and
                        hasattr(self.gui, 'window') and self.gui.window and
                        hasattr(self.gui.window, 'window')):
                    parent_window = self.gui.window.window

                dialog = Gtk.Window(title=title)
                dialog.set_modal(True)
                dialog.set_transient_for(parent_window)
                dialog.set_default_size(300, 150)
                dialog.set_resizable(False)

                box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
                box.set_margin_top(20)
                box.set_margin_bottom(20)
                box.set_margin_start(20)
                box.set_margin_end(20)

                label = Gtk.Label(label=message)
                label.set_wrap(True)
                label.set_selectable(True)
                box.append(label)

                btn_ok = Gtk.Button(label="OK")
                btn_ok.set_halign(Gtk.Align.CENTER)
                btn_ok.connect("clicked", lambda b: dialog.close())
                box.append(btn_ok)

                dialog.set_child(box)
                dialog.present()
                btn_ok.grab_focus()
            except Exception as e:
                print(f"{title}: {message}")
                print(f"Erreur affichage dialog: {e}")
            return False

        GLib.idle_add(_show_dialog)

    def visit_server_message(self, message: str, server: str):
        """Appelé depuis un thread réseau → déléguer au thread GTK."""
        if self._popup_pending:
            return  # ignore si une popup est déjà en attente
        self._popup_pending = True
        GLib.idle_add(self._handle_server_message, message, server)

    def _handle_server_message(self, message: str, server: str):
        try:
            self.show_message("Server Event", f"Server {server}: {message}")
        except Exception as e:
            print(f"Erreur dans _handle_server_message: {e}")
        finally:
            self._popup_pending = False  # libère le verrou
        return False
