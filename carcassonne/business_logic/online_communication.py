from __future__ import annotations
from typing import TYPE_CHECKING

from carcassonne.business_logic.game import Game

if TYPE_CHECKING:
    from carcassonne.business_logic.server import Server


class OnlineCommunication:

    def __init__(self, server: Server):
        self.server = server

    def command_ping(self) -> str:
        return "pong\n"

    def command_quit(self, client_username: str) -> str:
        self.server.repo.client_quit(client_username)
        return f"Bye {client_username}!\n"

    def command_server_status(self):
        assert (
            self.server.server
            is not None), "No server to execute the command on..."
        answer = f"Port: {self.server.server.getsockname()[1]}, "
        answer += f"Clients: {len(self.server.connected_clients)}, "
        answer += f"Current Parties: {len(self.server.current_games_list)}\n"
        return answer

    def command_new(self, message: str, client_id: str) -> str:
        message = message.split("new")[1]
        if message == "":
            return "You cannot create an empty party !"
        client_username = self.server.repo.get_username(client_id)
        # Create the group
        self.server.repo.create_party(client_username)
        clients_list = message.split(" ")
        # Check if the clients exist and are available,
        #  remove the ones that cannot be invited
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
            # Return a list of the current players (id, name and status)
            #  in the server, not the away players
            answer = self.server.repo.current_players()
        return answer

    def command_scoreboard(self) -> str:
        rows = self.server.repo.get_scoreboard()
        scoreboard: str = "Scoreboard:\n"
        for row in rows:
            scoreboard += f"Id: {row['id']}, username: {row['username']},"\
                f" victories: {row['victories']}, defeats: {row['defeats']},"\
                f" total games: {row['total_games']}\n"
        return scoreboard  # Affiche le tableau des scores
        # joueurs qui ont joué sur le serveur (nombre de
        # victoires, défaites, parties jouées) de la db.

    def command_accept(self, client_id: str) -> str:
        answer = ""
        if self.server.repo.invitation_received(client_id) == (0, 0):
            answer = "You have no invitation to accept.\n"
        else:
            sender_id, party_id = self.server.repo.invitation_received(
                client_id)
            # envoie à {self.invitation_received(client_id)}
            self.server.repo.accept_invitation(int(party_id), client_id)
            # Get invitee's name from repository
            self.notify_host_of_acceptance(sender_id, client_id)
            answer = "Invitation accepted!\n"
        return answer

    def command_decline(self, client_id: str) -> str:
        answer = ""
        if self.server.repo.invitation_received(client_id) == (0, 0):
            answer = "You have no invitation to decline.\n"
        else:
            host_id: int = self.server.repo.invitation_received(client_id)[0]
            # envoie à {self.invitation_received(client_id)}
            self.notify_host_of_rejection(host_id, client_id)
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
                message = f"Server -> {host_username}: {invitee_name}"\
                    "has accepted your invitation!\n"
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
                message = f"Server -> {host_username}: {invitee_name}"\
                    " has rejected your invitation!\n"
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
            answer = "No invitations to cancel."
        return answer

    def command_away(self, client_username):
        return self.server.repo.change_status(client_username, "away")

    def command_back(self, client_username):
        return self.server.repo.change_status(client_username, "idle")

    def command_play(self, message: str, client_id: str) -> str:
        game_id: int = self.server.repo.get_game(client_id)
        move: str = message.removeprefix("play ").strip()
        game: Game = self.server.current_games_list[game_id][1]
        board: str = game.get_printed_board()
        if game.end_game():
            return "You cannot play when the game is ended.\n" + board + "\n"
        if game.play_move(move):
            board: str = game.get_printed_board()
            group: int = self.server.repo.get_party_id(client_id)
            self.server.send_to_group(group, board)
            return "Move played.\n" + board + "\n"
        return "Move not played.\n" + board + "\n"

    def command_board(self, client_id: str) -> str:
        game_id: int = self.server.repo.get_game(client_id)
        game: Game = self.server.current_games_list[game_id][1]
        return game.get_printed_board()

    def command_set(self, client_id: str, message: str) -> str:
        content = message[3:].strip()
        if "=" in content:
            param, value = content.split("=", 1)
            param = param.strip()
            value = value.strip()
        else:
            param = content
            value = None
        game_id: int = self.server.repo.get_game(client_id)
        game: Game = self.server.current_games_list[game_id][1]
        game.set_game_configuration(param, value)
        return f"Paramètre '{param}' défini à '{value}'."

    def command_config(self, client_id: str) -> str:
        game_id: int = self.server.repo.get_game(client_id)
        game: Game = self.server.current_games_list[game_id][1]
        config = game.get_game_configuration()
        answer = "Configuration actuelle du jeu:"
        for key, value in config.items():
            answer += f"  {key}: {value}"
        return answer

    def command_history(self, client_id: str) -> str:
        game_id: int = self.server.repo.get_game(client_id)
        game: Game = self.server.current_games_list[game_id][1]
        history = game.get_history()
        answer = "Current history:"
        for move in history:
            answer += f" {move}"
        return answer

    def command_score(self, client_id: str) -> str:
        game_id: int = self.server.repo.get_game(client_id)
        game: Game = self.server.current_games_list[game_id][1]
        if game.end_game():
            game.score_manager.score_end_of_game(game.graph, game.players)
        else:
            game.score_manager.score_end_of_turn(game.graph, game.players)
        answer = "Score:"
        for player in game.players.values():
            answer += f"{player.get_username()} "\
                f"{'AI' if player.is_ai else ''}: {player.score} points.\n"
        return answer

    def command_hand(self, client_id: str) -> str:
        game_id: int = self.server.repo.get_game(client_id)
        game: Game = self.server.current_games_list[game_id][1]
        answer = ""
        if game.current_hand is None:
            answer = "Aucune tuile en main."
        else:
            answer = f"Tuile en main: {game.current_hand}"
        return answer

    def command_redo(self, client_id: str) -> str:
        game_id: int = self.server.repo.get_game(client_id)
        game: Game = self.server.current_games_list[game_id][1]
        game.redo()
        return "Derniers coups rétablis."

    def command_undo(self, client_id: str) -> str:
        game_id: int = self.server.repo.get_game(client_id)
        game: Game = self.server.current_games_list[game_id][1]
        game.undo()
        return "Derniers coups annulés."

    def command_hint(self, client_id: str) -> str:
        game_id: int = self.server.repo.get_game(client_id)
        game: Game = self.server.current_games_list[game_id][1]
        return game.provide_hint()

    def command_draw(self, client_id: str) -> str:
        game_id: int = self.server.repo.get_game(client_id)
        game: Game = self.server.current_games_list[game_id][1]
        already_had_tile: bool = game.current_hand is not None
        tile = game.draw_tile()
        answer = ""
        if tile is None:
            answer = "La pioche est vide!"
        elif already_had_tile:
            answer = "Vous avez déjà une tuile en main."
        else:
            answer = f"Tuile piochée: {tile}"
        return answer

    def command_shuffle(self, client_id: str) -> str:
        game_id: int = self.server.repo.get_game(client_id)
        game: Game = self.server.current_games_list[game_id][1]
        seed = game.shuffle_deck()
        return f"Pioche mélangée. Algo: {game.shuffle_algo}. Seed: {seed}"

    def command_save(self, client_id: str, message: str) -> str:
        filename = message[5:].strip()
        game_id: int = self.server.repo.get_game(client_id)
        game: Game = self.server.current_games_list[game_id][1]
        if game.save_game_to_file(filename) == 0:
            return f"Partie sauvegardée dans {filename}."
        return f"Erreur de la sauvegarde dans {filename}."

    def command_load(self, client_id: str, message: str) -> str:
        filename = message[5:].strip()
        game_id: int = self.server.repo.get_game(client_id)
        game: Game = self.server.current_games_list[game_id][1]
        if game.load_game_from_file(filename) == 0:
            return f"Partie chargée depuis {filename}."
        return f"Erreur du chargement depuis {filename}."
