from gi.repository import Gtk
import os

import gi

gi.require_version("Gtk", "4.0")


class InvitationMenu(Gtk.Box):
    """Menu for managing party invitations.

    This menu provides controls for sending invitations, accepting/declining
    invitations, managing player status, and viewing player information.
    """

    def __init__(self, gui):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        self.gui = gui

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

        title = Gtk.Label(label="Party Invitations")
        title.add_css_class("section-title")
        self.main_box.append(title)

        self.append(self.main_box)

        # --- Player Information Section -----------------------------------
        info_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)

        info_title = Gtk.Label(label="Player Information")
        info_title.add_css_class("section-title")
        info_box.append(info_title)

        # Player ID input for details
        player_id_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        player_id_box.set_halign(Gtk.Align.CENTER)
        player_id_label = Gtk.Label(label="Player ID:")
        self.entry_player_id = Gtk.Entry()
        self.entry_player_id.set_placeholder_text(
            "Enter player ID or leave empty for all")
        player_id_box.append(player_id_label)
        player_id_box.append(self.entry_player_id)
        info_box.append(player_id_box)

        # Show players button
        btn_show_players = Gtk.Button(label="Show Players")
        btn_show_players.add_css_class("back-buttons")
        btn_show_players.connect("clicked", self.on_show_players)
        info_box.append(btn_show_players)

        self.main_box.append(info_box)

        # --- Invitation Management Section ---------------------------------
        invitation_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)

        invitation_title = Gtk.Label(label="Invitation Management")
        invitation_title.add_css_class("section-title")
        invitation_box.append(invitation_title)

        # Send invitation section
        send_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        send_box.set_halign(Gtk.Align.CENTER)
        send_label = Gtk.Label(label="Invite Player ID:")
        self.entry_invite_id = Gtk.Entry()
        self.entry_invite_id.set_placeholder_text("Player ID to invite")
        btn_send_invite = Gtk.Button(label="Send Invitation")
        btn_send_invite.add_css_class("back-buttons")
        btn_send_invite.connect("clicked", self.on_send_invitation)
        send_box.append(send_label)
        send_box.append(self.entry_invite_id)
        send_box.append(btn_send_invite)
        invitation_box.append(send_box)

        # Response buttons
        response_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        response_box.set_halign(Gtk.Align.CENTER)

        btn_accept = Gtk.Button(label="Accept Invitation")
        btn_accept.add_css_class("back-buttons")
        btn_accept.connect("clicked", self.on_accept_invitation)
        response_box.append(btn_accept)

        btn_decline = Gtk.Button(label="Decline Invitation")
        btn_decline.add_css_class("back-buttons")
        btn_decline.connect("clicked", self.on_decline_invitation)
        response_box.append(btn_decline)

        btn_cancel = Gtk.Button(label="Cancel Invitation")
        btn_cancel.add_css_class("back-buttons")
        btn_cancel.connect("clicked", self.on_cancel_invitation)
        response_box.append(btn_cancel)

        invitation_box.append(response_box)

        self.main_box.append(invitation_box)

        # --- Status Management Section ---------------------------------
        status_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=6)

        status_title = Gtk.Label(label="Status Management")
        status_title.add_css_class("section-title")
        status_box.append(status_title)

        # Status buttons
        status_buttons_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        status_buttons_box.set_halign(Gtk.Align.CENTER)

        btn_away = Gtk.Button(label="Set Away")
        btn_away.add_css_class("back-buttons")
        btn_away.connect("clicked", self.on_set_away)
        status_buttons_box.append(btn_away)

        btn_back_idle = Gtk.Button(label="Back to Idle")
        btn_back_idle.add_css_class("back-buttons")
        btn_back_idle.connect("clicked", self.on_back_to_idle)
        status_buttons_box.append(btn_back_idle)

        status_box.append(status_buttons_box)

        self.main_box.append(status_box)

        # --- Back Button -------------------------------------------------

        btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        btn_back = Gtk.Button(label="Back to Multiplayer")
        btn_back.add_css_class("quit-button")
        btn_back.connect("clicked", self.on_back)
        btn_back.set_hexpand(False)

        btn_box.set_halign(Gtk.Align.CENTER)
        btn_box.append(btn_back)

        self.main_box.append(btn_box)

    # ------------------------------------------------------------------

    def on_show_players(self, button):
        """Show player information."""
        player_id = self.entry_player_id.get_text().strip()

        try:
            if player_id:
                # Show specific player details
                player_profile = self.gui.game_data.client.repo.get_player_profile(
                    int(player_id))
                if player_profile:
                    player_text = f"Player ID: {player_id}\n"
                    player_text += f"Username: {player_profile.get('username', 'N/A')}\n"
                    player_text += f"Status: {player_profile.get('status', 'N/A')}\n"
                    player_text += f"Wins: {player_profile.get('stats_win', 0)}\n"
                    player_text += f"Losses: {player_profile.get('stats_lose', 0)}\n"
                    player_text += f"Score: {player_profile.get('score', 0)}"
                else:
                    player_text = f"No player found with ID {player_id}"
            else:
                # Show all players
                scoreboard = self.gui.game_data.client.repo.get_scoreboard()
                if scoreboard:
                    player_text = "\n".join([
                        f"ID: {self.gui.game_data.client.repo.get_id_from_username(p['username'])}, "
                        f"Name: {p['username']}, "
                        f"Status: {self.gui.game_data.client.repo.get_status(str(self.gui.game_data.client.repo.get_id_from_username(p['username'])))}"
                        for p in scoreboard
                    ])
                else:
                    player_text = "No players found"

            self.show_message("Player Information", player_text)
        except Exception as e:
            print(f"Error getting player info: {e}")
            self.show_message(
                "Error", f"Error getting player information: {e}")

    def on_send_invitation(self, button):
        """Send an invitation to a player."""
        invite_id = self.entry_invite_id.get_text().strip()
        if not invite_id:
            self.show_message("Error", "Please enter a player ID to invite")
            return

        try:
            # Check if player exists and is not away
            player_profile = self.gui.game_data.client.repo.get_player_profile(
                int(invite_id))
            if not player_profile:
                self.show_message(
                    "Error", f"Player {invite_id} does not exist")
                return

            status = self.gui.game_data.client.repo.get_status(invite_id)
            if status == "away":
                self.show_message(
                    "Error", f"Player {invite_id} is away and cannot receive invitations")
                return

            # Send invitation
            current_player_id = str(self.gui.game_data.client.repo.get_id_from_username(
                self.gui.game_data.client.client_player))
            result = self.gui.game_data.client.repo.send_invitation(
                current_player_id, invite_id)

            if result:
                self.show_message(
                    "Success", f"Invitation sent to player {invite_id}")
            else:
                self.show_message(
                    "Error", f"Failed to send invitation to player {invite_id}")
        except Exception as e:
            print(f"Error sending invitation: {e}")
            self.show_message("Error", f"Error sending invitation: {e}")

    def on_accept_invitation(self, button):
        """Accept the current invitation."""
        try:
            current_player_id = str(self.gui.game_data.client.repo.get_id_from_username(
                self.gui.game_data.client.client_player))
            invitation = self.gui.game_data.client.repo.invitation_received(
                current_player_id)

            if invitation == (-1, -1):
                self.show_message("Error", "No pending invitation to accept")
                return

            self.gui.game_data.client.repo.accept_invitation(
                invitation[1], current_player_id)
            self.show_message(
                "Success", "Invitation accepted. Game will start soon.")
        except Exception as e:
            print(f"Error accepting invitation: {e}")
            self.show_message("Error", f"Error accepting invitation: {e}")

    def on_decline_invitation(self, button):
        """Decline the current invitation."""
        try:
            current_player_id = str(self.gui.game_data.client.repo.get_id_from_username(
                self.gui.game_data.client.client_player))
            invitation = self.gui.game_data.client.repo.invitation_received(
                current_player_id)

            if invitation == (-1, -1):
                self.show_message("Error", "No pending invitation to decline")
                return

            self.gui.game_data.client.repo.reject_invitation(current_player_id)
            self.show_message("Success", "Invitation declined")
        except Exception as e:
            print(f"Error declining invitation: {e}")
            self.show_message("Error", f"Error declining invitation: {e}")

    def on_cancel_invitation(self, button):
        """Cancel a sent invitation."""
        try:
            current_player_id = str(self.gui.game_data.client.repo.get_id_from_username(
                self.gui.game_data.client.client_player))
            players_to_cancel = self.gui.game_data.client.repo.invitation_sent_from(
                current_player_id)

            if not players_to_cancel:
                self.show_message("Error", "No pending invitations to cancel")
                return

            # Cancel all pending invitations
            result = self.gui.game_data.client.repo.cancel_invitation_from(
                current_player_id, players_to_cancel)
            self.show_message("Success", f"Invitations cancelled: {result}")
        except Exception as e:
            print(f"Error cancelling invitation: {e}")
            self.show_message("Error", f"Error cancelling invitation: {e}")

    def on_set_away(self, button):
        """Set player status to away."""
        try:
            current_player_id = str(self.gui.game_data.client.repo.get_id_from_username(
                self.gui.game_data.client.client_player))
            result = self.gui.game_data.client.repo.change_status(
                current_player_id, "away")
            self.show_message("Success", "Status set to away")
        except Exception as e:
            print(f"Error setting status to away: {e}")
            self.show_message("Error", f"Error setting status to away: {e}")

    def on_back_to_idle(self, button):
        """Set player status back to idle."""
        try:
            current_player_id = str(self.gui.game_data.client.repo.get_id_from_username(
                self.gui.game_data.client.client_player))
            result = self.gui.game_data.client.repo.change_status(
                current_player_id, "idle")
            self.show_message("Success", "Status set back to idle")
        except Exception as e:
            print(f"Error setting status to idle: {e}")
            self.show_message("Error", f"Error setting status to idle: {e}")

    def on_back(self, button):
        """Return to the multiplayer menu."""
        self.gui.window.stack.set_visible_child_name("multiplayer_menu")

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
