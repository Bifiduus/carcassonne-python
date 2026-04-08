import sys
from gi.repository import Gtk, GLib
import ast

import gi

from carcassonne.i18n import gettext as _
from carcassonne.interfaces.i_client_service import IClientService

gi.require_version("Gtk", "4.0")


class InvitationMenu(Gtk.Box):
    """Menu for managing party invitations.

    This menu provides controls for sending invitations, accepting/declining
    invitations, managing player status, and viewing player information.

    Follows 3-tier architecture by depending on IClientService interface.
    """

    def __init__(self, gui, client_service: IClientService = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        self.gui = gui
        # Use interface for client service (3-tier architecture)
        self.client_service = client_service or (
            gui.game_data.client if gui.game_data else None)

        # store last visitor message for external retrieval / tests
        self.last_server_message = None
        self.last_server_name = None
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

        title = Gtk.Label(label=_("Party invitations"))
        title.add_css_class("section-title")
        self.main_box.append(title)

        self.append(self.main_box)

        # --- Player Information Section -----------------------------------
        info_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)

        info_title = Gtk.Label(label=_("Player information"))
        info_title.add_css_class("section-title")
        info_box.append(info_title)

        # Player ID input for details
        player_id_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        player_id_box.set_halign(Gtk.Align.CENTER)
        player_id_label = Gtk.Label(label=_("Player ID:"))
        self.entry_player_id = Gtk.Entry()
        self.entry_player_id.set_placeholder_text(
            _("Enter player ID or leave empty for all")
        )
        player_id_box.append(player_id_label)
        player_id_box.append(self.entry_player_id)
        info_box.append(player_id_box)

        # Show players button
        btn_show_players = Gtk.Button(label=_("Show players"))
        btn_show_players.add_css_class("orange-buttons")
        btn_show_players.connect("clicked", self.on_show_players)
        info_box.append(btn_show_players)

        self.main_box.append(info_box)

        # --- Invitation Management Section ---------------------------------
        invitation_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)

        invitation_title = Gtk.Label(label=_("Invitation management"))
        invitation_title.add_css_class("section-title")
        invitation_box.append(invitation_title)

        # Send invitation section
        send_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        send_box.set_halign(Gtk.Align.CENTER)
        send_label = Gtk.Label(label=_("Invite player ID:"))
        self.entry_invite_id = Gtk.Entry()
        self.entry_invite_id.set_placeholder_text(_("Player ID to invite"))
        btn_send_invite = Gtk.Button(label=_("Send invitation"))
        btn_send_invite.add_css_class("orange-buttons")
        btn_send_invite.connect("clicked", self.on_send_invitation)
        send_box.append(send_label)
        send_box.append(self.entry_invite_id)
        send_box.append(btn_send_invite)
        invitation_box.append(send_box)

        # Response buttons
        response_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        response_box.set_halign(Gtk.Align.CENTER)

        btn_accept = Gtk.Button(label=_("Accept invitation"))
        btn_accept.add_css_class("orange-buttons")
        btn_accept.connect("clicked", self.on_accept_invitation)
        response_box.append(btn_accept)

        btn_decline = Gtk.Button(label=_("Decline invitation"))
        btn_decline.add_css_class("orange-buttons")
        btn_decline.connect("clicked", self.on_decline_invitation)
        response_box.append(btn_decline)

        btn_cancel = Gtk.Button(label=_("Cancel invitation"))
        btn_cancel.add_css_class("orange-buttons")
        btn_cancel.connect("clicked", self.on_cancel_invitation)
        response_box.append(btn_cancel)

        invitation_box.append(response_box)

        self.main_box.append(invitation_box)

        # --- Status Management Section ---------------------------------
        status_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)

        status_title = Gtk.Label(label=_("Status management"))
        status_title.add_css_class("section-title")
        status_box.append(status_title)

        # Status buttons
        status_buttons_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        status_buttons_box.set_halign(Gtk.Align.CENTER)

        btn_away = Gtk.Button(label=_("Set away"))
        btn_away.add_css_class("orange-buttons")
        btn_away.connect("clicked", self.on_set_away)
        status_buttons_box.append(btn_away)

        btn_back_idle = Gtk.Button(label=_("Back to idle"))
        btn_back_idle.add_css_class("orange-buttons")
        btn_back_idle.connect("clicked", self.on_back_to_idle)
        status_buttons_box.append(btn_back_idle)

        status_box.append(status_buttons_box)

        self.main_box.append(status_box)

        # --- Back Button -------------------------------------------------

        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        btn_back = Gtk.Button(label=_("Back to multiplayer"))
        btn_back.add_css_class("red-buttons")
        btn_back.connect("clicked", self.on_back)
        btn_back.set_hexpand(False)

        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.append(btn_back)

        self.main_box.append(btn_box)

    # ------------------------------------------------------------------

    def on_show_players(self, button):
        """Show player information; response comes via the visitor."""
        player_id = self.entry_player_id.get_text().strip()
        try:
            message = "players " + player_id if player_id else "players"
            result = self.client_service.send_to_server(message)
            if not result:
                self.show_message(
                    _("Error"),
                    _("Unable to send the request."),
                )
            # No popup here: response arrives via visit_server_message()
        except Exception as e:
            self.show_message(
                _("Error"),
                _("Error: {error}").format(error=e),
            )

    def on_send_invitation(self, button):
        """Send an invitation to a player."""
        invite_id = self.entry_invite_id.get_text().strip()
        if not invite_id:
            self.show_message(
                _("Error"),
                _("Please enter a player ID to invite."),
            )
            return

        try:
            result = self.client_service.send_to_server(
                "new " + invite_id)
            if not result:
                self.show_message(
                    _("Error"),
                    _("Failed to send invitation request."),
                )
            # Response will arrive via visit_server_message() from server
        except Exception as e:
            print(f"Error sending invitation: {e}", file=sys.stderr)
            self.show_message(
                _("Error"),
                _("Error sending invitation: {error}").format(error=e),
            )

    def on_accept_invitation(self, button):
        """Accept the current invitation."""
        try:
            result = self.client_service.send_to_server("accept")
            if not result:
                self.show_message(
                    _("Error"),
                    _("Failed to send acceptance."),
                )
            # Response will arrive via visit_server_message() from server
        except Exception as e:
            print(f"Error accepting invitation: {e}", file=sys.stderr)
            self.show_message(
                _("Error"),
                _("Error accepting invitation: {error}").format(error=e),
            )

    def on_decline_invitation(self, button):
        """Decline the current invitation."""
        try:
            result = self.client_service.send_to_server("decline")
            if not result:
                self.show_message(
                    _("Error"),
                    _("Failed to send decline response."),
                )
            # Response will arrive via visit_server_message() from server
        except Exception as e:
            print(f"Error declining invitation: {e}", file=sys.stderr)
            self.show_message(
                _("Error"),
                _("Error declining invitation: {error}").format(error=e),
            )

    def on_cancel_invitation(self, button):
        """Cancel a sent invitation."""
        try:
            result = self.client_service.send_to_server("cancel")
            if not result:
                self.show_message(
                    _("Error"),
                    _("Failed to send cancellation."),
                )
            # Response will arrive via visit_server_message() from server
        except Exception as e:
            print(f"Error cancelling invitation: {e}", file=sys.stderr)
            self.show_message(
                _("Error"),
                _("Error cancelling invitation: {error}").format(error=e),
            )

    def on_set_away(self, button):
        """Set player status to away."""
        try:
            result = self.client_service.send_to_server("away")
            if not result:
                self.show_message(
                    _("Error"),
                    _("Failed to send away status."),
                )
            # Response will arrive via visit_server_message() from server
        except Exception as e:
            print(f"Error setting status to away: {e}", file=sys.stderr)
            self.show_message(
                _("Error"),
                _("Error setting status to away: {error}").format(error=e),
            )

    def on_back_to_idle(self, button):
        """Set player status back to idle."""
        try:
            result = self.client_service.send_to_server("back")
            if not result:
                self.show_message(
                    _("Error"),
                    _("Failed to send idle status."),
                )
            # Response will arrive via visit_server_message() from server
        except Exception as e:
            print(f"Error setting status to idle: {e}", file=sys.stderr)
            self.show_message(
                _("Error"),
                _("Error setting status to idle: {error}").format(error=e),
            )

    def on_back(self, button):
        """Return to the multiplayer menu."""
        self.gui.window.stack.set_visible_child_name("multiplayer_menu")

    def show_message(self, title: str, received):
        """Show a message dialog (GTK4 compatible)."""
        if isinstance(received, bool):
            message = _("Success") if received else _("Failure")
        elif received is None:
            message = _("No response received.")
        else:
            message = str(received)

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

                btn_ok = Gtk.Button(label=_("OK"))
                btn_ok.set_halign(Gtk.Align.CENTER)
                btn_ok.connect("clicked", lambda b: dialog.close())
                box.append(btn_ok)

                dialog.set_child(box)
                dialog.present()
                btn_ok.grab_focus()
            except Exception as e:
                print(f"{title}: {message}")
                print(f"Dialog display error: {e}")
            return False

        GLib.idle_add(_show_dialog)

    def visit_server_message(self, message: str, server: str):
        """Called from a network thread -> delegate to GTK thread."""
        if self._popup_pending:
            return  # ignore if a popup is already pending
        self._popup_pending = True
        self.last_server_message = message
        self.last_server_name = server
        # Schedule display on the GTK main thread
        GLib.idle_add(self._handle_server_message, message, server)

    def _handle_server_message(self, message: str, server: str):
        """Executed on the GTK main thread."""
        try:
            if "List of current players:" in message:
                self._display_player_list(message)
            else:
                self.show_message(
                    _("Server event"),
                    _("Server {server}: {message}").format(
                        server=server,
                        message=message,
                    ),
                )
        except Exception as e:
            print(f"Error in _handle_server_message: {e}")
        finally:
            self._popup_pending = False  # release lock
        # Important: tell GLib not to call this function again.
        return False

    def _display_player_list(self, message: str):
        """Display the player list safely."""
        try:
            prefixes = [
                _("List of current players: "),
                "List of current players: ",
            ]
            list_str = None
            for prefix in prefixes:
                if message.startswith(prefix):
                    list_str = message.split(prefix, 1)[1]
                    break
            if list_str is None:
                raise ValueError("players prefix not found")
            players_list = ast.literal_eval(list_str)

            if not players_list:
                self.show_message(
                    _("Connected players"),
                    _("No players connected."),
                )
                return

            lines = [_("{id_col:<6} {name_col:<20} {status_col}").format(
                id_col="ID",
                name_col=_("Name"),
                status_col=_("Status"),
            )]
            lines.append("─" * 36)
            for entry in players_list:
                player_id, username, status = entry
                lines.append(f"{str(player_id):<6} {username:<20} {status}")

            self.show_message(_("Connected players"), "\n".join(lines))

        except (ValueError, SyntaxError, IndexError) as e:
            print(f"Error parsing players list: {e}")
            self.show_message(
                _("Connected players"),
                _("Raw response:\n{message}").format(message=message),
            )
        except Exception as e:
            print(f"Error in _display_player_list: {e}")
            self.show_message(
                _("Error"),
                _("Error while displaying: {error}").format(error=e),
            )

    def get_last_server_event(self):
        """Return the last received server event (server, message)."""
        return self.last_server_name, self.last_server_message
