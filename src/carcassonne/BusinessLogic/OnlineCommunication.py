from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from carcassonne.BusinessLogic.Server import Server


class OnlineCommunication:

    def __init__(self, server: Server):
        self.server = server

    def command_ping(self) -> str:
        return "pong\n"

    def command_quit(self, client_username: str) -> str:
        return f"Bye {client_username}!\n"

    def command_server_status(self):
        assert (
            self.server.server is not None), "No server to execute the command on..."
        answer = f"Port: { self.server.server.getsockname()[1]}, "
        answer += f"Clients: {len(self.server.connected_clients)}, "
        answer += f"Current Parties: {len(self.server.current_games_list)}\n"
        return answer

    def command_new(self, message: str, client_id: str) -> str:
        message = message.split("new")[1]
        party_name = f"Party {len(self.server.current_games_list)}"
        clients_list = message.split(" ")
        # Check if the clients exist and are available, remove the ones that cannot be invited
        clients_list_checked = self.server.check_clients_list_validity(
            clients_list)
        for invited in clients_list_checked:
            self.server.send_invitation(invited, client_id)
        # Create a new party with a name and players, ask them first

        answer = "Invitation(s) sent."
        return answer

    def command_players(self, message: str) -> str:
        answer = ""
        if message.removeprefix("players") != "":
            answer = self.server.check_profile_player(
                int(message.split("players")[1].strip()))
        else:
            # Return a list of the current players (id, name and status) in the server, not the away players
            answer = self.server.repo.current_players()
        return answer

    def command_scoreboard(self) -> str:
        rows = self.server.repo.get_scoreboard()
        scoreboard: str = "Scoreboard:\n"
        for row in rows:
            scoreboard += f"Id: {row['id']}, username: {row['username']},"\
                f" victories: {row['victories']}, defeats: {row['defeats']}, total games: {row['total_games']}\n"
        return scoreboard  # Affiche le tableau des scores
        # joueurs qui ont joué sur le serveur (nombre de
        # victoires, défaites, parties jouées) de la db.

    def command_accept(self, client_id: str) -> str:
        answer = ""
        sender, party_id = self.server.repo.invitation_received(
            client_id)
        if sender == -1:
            answer = f"You have no invitation to accept.\n"
        else:
            # envoie à {self.invitation_received(client_id)}
            self.server.repo.accept_invitation(int(party_id), client_id)
            # Get invitee's name from repository
            self.notify_host_of_acceptance(sender, client_id)
            answer = f"Invitation accepted!\n"
        return answer

    def command_decline(self, client_id: str) -> str:
        answer = ""
        if self.server.repo.invitation_received(client_id) != -1:
            answer = f"You have no invitation to decline.\n"
        else:
            host_id: str = self.server.repo.invitation_received(client_id)[
                'host_player']
            # envoie à {self.invitation_received(client_id)}
            self.notify_host_of_rejection(int(host_id), client_id)
            answer = ""
        return answer

    def notify_host_of_acceptance(self, host_id: int, invitee_id: str):
        """Send notification to host that an invitation was accepted."""
        if host_id in self.server.client_sockets:
            try:
                host_username: str = self.server.repo.get_username(
                    str(host_id))
                invitee_name: str = self.server.repo.get_username(
                    invitee_id
                )
                host_socket = self.server.client_sockets[host_id]
                message = f"Server -> {host_username}: {invitee_name} has accepted your invitation!\n"
                host_socket.send(message.encode())
            except Exception as e:
                print(f"Error notifying host {host_id}: {e}")

    def notify_host_of_rejection(self, host_id: int, invitee_id: str):
        """Send notification to host that an invitation was rejected."""
        if host_id in self.server.client_sockets:
            try:
                host_username: str = self.server.repo.get_username(
                    str(host_id))
                invitee_name: str = self.server.repo.get_username(
                    invitee_id
                )
                host_socket = self.server.client_sockets[host_id]
                message = f"Server -> {host_username}: {invitee_name} has rejected your invitation!\n"
                host_socket.send(message.encode())
            except Exception as e:
                print(f"Error notifying host {host_id}: {e}")

    def command_cancel(self, client_id: str, players: str) -> str:
        answer = ""
        if self.server.repo.invitation_sent_from(client_id):
            # des invitations en attentes, envoie des messages
            players_list = players.split(" ")
            answer = self.server.repo.cancel_invitation_from(
                client_id, players_list)
        else:
            answer = f"No invitations to cancel."
        return answer

    def command_away(self, client_username):
        return self.server.repo.change_status(client_username, "away")

    def command_back(self, client_username):
        # change to previous status ?
        return self.server.repo.change_status(client_username, "idle")
