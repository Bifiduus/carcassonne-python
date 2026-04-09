from __future__ import annotations
from time import time
import sys
from typing import TYPE_CHECKING

from carcassonne.business_logic.game.game import Game
from carcassonne.i18n import gettext as _

if TYPE_CHECKING:
    from carcassonne.business_logic.server import Server


class OnlineCommunication:

    def __init__(self, server: Server):
        self.server = server

    def command_ping(self, message: str) -> str:
        previous_time = float(message.removeprefix("ping "))
        return f"pong\nTime is {time()-previous_time}ms"

    def command_quit(self, client_username: str) -> str:
        self.server.repo.client_quit(client_username)
        return _("Bye {username}!").format(username=client_username) + "\n"

    def command_server_status(self):
        assert (
            self.server.server is not None
        ), "No server to execute the command on..."
        answer = _(
            "Port: {port}, Clients: {clients}, Current parties: {parties}"
        ).format(
            port=self.server.server.getsockname()[1],
            clients=len(self.server.connected_clients),
            parties=len(self.server.current_games_list),
        )
        answer += "\n"
        return answer

    def command_new(self, message: str, client_id: str) -> str:
        message = message.split("new")[1]
        if message == "":
            return "You cannot create an empty party !"
        client_username = self.server.repo.get_username(client_id)
        # Create the group
        self.server.repo.create_party(client_username)
        clients_list = message.strip().split(" ")
        # Check if the clients exist and are available,
        #  remove the ones that cannot be invited
        clients_list_checked = self.server.check_clients_list_validity(
            clients_list
        )
        for invited in clients_list_checked:
            self.server.send_invitation(invited, client_id)
        # Create a new party with a name and players, ask them first

        answer = "Invitation(s) sent."
        return answer

    def command_players(self, message: str) -> str:
        answer = ""
        if message.removeprefix("players") != "":
            answer = self.server.check_profile_player(
                int(message.split("players")[1].strip())
            )
        else:
            # Return a list of the current players (id, name and status)
            #  in the server, not the away players
            answer = self.server.repo.current_players()
        return answer

    def command_scoreboard(self) -> str:
        rows = self.server.repo.get_scoreboard()
        scoreboard: str = _("Scoreboard:") + "\n"
        for row in rows:
            scoreboard += (
                _(
                    "Id: {id}, username: {username}, victories: {victories}, "
                    "defeats: {defeats}, total games: {total_games}"
                ).format(
                    id=row["id"],
                    username=row["username"],
                    victories=row["victories"],
                    defeats=row["defeats"],
                    total_games=row["total_games"],
                )
                + "\n"
            )
        return scoreboard  # Display the scoreboard table
        # players who played on the server (wins,
        # losses, total games) from the database.

    def command_accept(self, client_id: str) -> str:
        answer = ""
        if self.server.repo.invitation_received(client_id) == (-1, -1):
            answer = "You have no invitation to accept.\n"
        else:
            sender_id, party_id = self.server.repo.invitation_received(
                client_id
            )
            self.server.repo.accept_invitation(int(party_id), client_id)
            self.notify_host_of_acceptance(sender_id, client_id)
            answer = "Invitation accepted !\n"
        return answer

    def command_decline(self, client_id: str) -> str:
        answer = ""
        if self.server.repo.invitation_received(client_id) == (-1, -1):
            answer = "You have no invitation to decline.\n"
        else:
            host_id: int = self.server.repo.invitation_received(client_id)[0]
            self.server.repo.reject_invitation(client_id)
            self.notify_host_of_rejection(host_id, client_id)
            answer = "Invitation declined !\n"
        return answer

    def notify_host_of_acceptance(self, host_id: int, invitee_id: str):
        """Send notification to host that an invitation was accepted."""
        if host_id in self.server.client_sockets:
            try:
                invitee_name: str = self.server.repo.get_username(invitee_id)
                host_socket = self.server.client_sockets[host_id]
                message = (
                    _("{invitee_name} has accepted your invitation!").format(
                        invitee_name=invitee_name
                    )
                    + "\n"
                )
                host_socket.send(message.encode())
            except Exception as e:
                print(f"Error notifying host {host_id}: {e}", file=sys.stderr)

    def notify_host_of_rejection(self, host_id: int, invitee_id: str):
        """Send notification to host that an invitation was rejected."""
        if host_id in self.server.client_sockets:
            try:
                invitee_name: str = self.server.repo.get_username(invitee_id)
                host_socket = self.server.client_sockets[host_id]
                message = (
                    _("{invitee_name} has rejected your invitation!").format(
                        invitee_name=invitee_name
                    )
                    + "\n"
                )
                host_socket.send(message.encode())
            except Exception as e:
                print(f"Error notifying host {host_id}: {e}", file=sys.stderr)

    def command_cancel(self, client_id: str, players: str) -> str:
        answer = ""
        if self.server.repo.invitation_sent_from(client_id):
            # des invitations en attentes, envoie des messages
            players_list = []
            if players != "":
                players_list = players.split(" ")
            answer = self.server.repo.cancel_invitation_from(
                client_id, players_list
            )
        else:
            answer = "No invitations to cancel."
        return answer

    def command_away(self, client_username):
        return self.server.repo.change_status(client_username, "away")

    def command_back(self, client_username):
        return self.server.repo.change_status(client_username, "idle")

    def command_play(self, message: str, client_id: str) -> str:
        if self.server.repo.get_party_id(client_id) == -1:
            return "You are not in a game."
        party_id = self.server.repo.get_party_id(client_id)
        game_id: int = self.server.repo.get_game_id(party_id)
        move: str = message.removeprefix("play ").strip()
        game: Game = self.server.current_games_list[game_id][1]
        if game.get_current_player().get_id() != int(client_id):
            return "It is not your turn to play"
        if game.end_game():
            board: str = game.get_printed_board()
            return "You cannot play when the game is ended.\n" + board + "\n"
        if game.play_move(move):
            board: str = game.get_printed_board()
            # Send board update to OTHER players (not the current player)
            board_message = f"OPPONENT_MOVE played move. Board:\n{board}\n"
            client_username = self.server.repo.get_username(client_id)
            self.server.send_to_group_except(
                party_id,
                board_message,
                client_username,
            )
            return "Move played.\n" + board + "\n"
        board: str = game.get_printed_board()
        return "Move not played.\n" + board + "\n"

    def command_board(self, client_id: str) -> str:
        if self.server.repo.get_party_id(client_id) == -1:
            return "You are not in a game."
        party_id = self.server.repo.get_party_id(client_id)
        game_id: int = self.server.repo.get_game_id(party_id)
        game: Game = self.server.current_games_list[game_id][1]
        return "Game board:\n" + game.get_printed_board()

    def command_set(self, client_id: str, message: str) -> str:
        if self.server.repo.get_party_id(client_id) == -1:
            return "You are not in a game."
        content = message[3:].strip()
        if "=" not in content:
            return "Usage: set PARAM=VALUE"
        param, value = content.split("=", 1)
        param = param.strip()
        value = value.strip()
        if not param:
            return "Usage: set PARAM=VALUE"
        party_id = self.server.repo.get_party_id(client_id)
        game_id: int = self.server.repo.get_game_id(party_id)
        game: Game = self.server.current_games_list[game_id][1]
        try:
            param, value = game.set_game_configuration(param, value)
        except KeyError as error:
            return "Invalid configuration parameter: " + str(error.args[0])
        except (TypeError, ValueError) as error:
            return "Invalid configuration parameter: " + str(error)
        return _("Parameter '{param}' set to '{value}'.").format(
            param=param,
            value=value,
        )

    def command_config(self, client_id: str) -> str:
        party_id = self.server.repo.get_party_id(client_id)
        game_id: int = self.server.repo.get_game_id(party_id)
        game: Game = self.server.current_games_list[game_id][1]
        config = game.get_game_configuration()
        answer = _("Current game configuration:")
        for key, value in config.items():
            answer += f"  {key}: {value}"
        return answer

    def command_history(self, client_id: str) -> str:
        if self.server.repo.get_party_id(client_id) == -1:
            return "You are not in a game."
        party_id = self.server.repo.get_party_id(client_id)
        game_id: int = self.server.repo.get_game_id(party_id)
        game: Game = self.server.current_games_list[game_id][1]
        history = game.get_history()
        answer = _("Current history:")
        for move in history:
            answer += f" {move}"
        return answer

    def command_score(self, client_id: str) -> str:
        if self.server.repo.get_party_id(client_id) == -1:
            return "You are not in a game."
        party_id = self.server.repo.get_party_id(client_id)
        game_id: int = self.server.repo.get_game_id(party_id)
        game: Game = self.server.current_games_list[game_id][1]
        game.end_game()
        answer = _("Score:")
        for player in game.game_data.players.values():
            player_label = player.get_username()
            if player.is_ai:
                player_label = f"{player_label} {_('AI')}"
            answer += _("{player}: {score} points.").format(
                player=player_label,
                score=player.score,
            ) + "\n"
        return answer

    def command_hand(self, client_id: str) -> str:
        if self.server.repo.get_party_id(client_id) == -1:
            return "You are not in a game."
        party_id = self.server.repo.get_party_id(client_id)
        game_id: int = self.server.repo.get_game_id(party_id)
        game: Game = self.server.current_games_list[game_id][1]
        answer = ""
        if game.game_data.current_hand is None:
            answer = _("No tile in hand.")
        else:
            answer = _("Tile in hand: {tile}").format(
                tile=game.game_data.current_hand
            )
        return answer

    @staticmethod
    def _parse_optional_count(message: str, command: str) -> int:
        suffix = message.removeprefix(command).strip()
        if suffix == "":
            return 1
        count = int(suffix)
        if count < 1:
            raise ValueError
        return count

    def command_redo(self, message: str, client_id: str) -> str:
        if self.server.repo.get_party_id(client_id) == -1:
            return "You are not in a game."
        party_id = self.server.repo.get_party_id(client_id)
        game_id: int = self.server.repo.get_game_id(party_id)
        game: Game = self.server.current_games_list[game_id][1]
        if game.get_current_player().get_id() != int(client_id):
            return "It is not your turn to play"
        try:
            count = self._parse_optional_count(message, "redo")
        except ValueError:
            return "Usage: redo [N]"
        redone = game.redo_moves(count)
        if redone == 0:
            return _("No move to redo.")
        # Notify other players about the board state change
        board: str = game.get_printed_board()
        board_message = f"OPPONENT_MOVE redone moves. Board:\n{board}\n"
        client_username = self.server.repo.get_username(client_id)
        self.server.send_to_group_except(
            party_id,
            board_message,
            client_username,
        )
        return _("Last {count} move(s) redone.").format(count=count)

    def command_undo(self, message: str, client_id: str) -> str:
        if self.server.repo.get_party_id(client_id) == -1:
            return "You are not in a game."
        party_id = self.server.repo.get_party_id(client_id)
        game_id: int = self.server.repo.get_game_id(party_id)
        game: Game = self.server.current_games_list[game_id][1]
        if game.get_current_player().get_id() != int(client_id):
            return "It is not your turn to play"
        try:
            count = self._parse_optional_count(message, "undo")
        except ValueError:
            return "Usage: undo [N]"
        undone = game.undo_moves(count)
        if undone == 0:
            return _("No move to undo.")
        # Notify other players about the board state change
        board: str = game.get_printed_board()
        board_message = f"OPPONENT_MOVE undone moves. Board:\n{board}\n"
        client_username = self.server.repo.get_username(client_id)
        self.server.send_to_group_except(
            party_id,
            board_message,
            client_username,
        )
        return _("Last {count} move(s) undone.").format(count=count)

    def command_hint(self, client_id: str) -> str:
        if self.server.repo.get_party_id(client_id) == -1:
            return "You are not in a game."
        party_id = self.server.repo.get_party_id(client_id)
        game_id: int = self.server.repo.get_game_id(party_id)
        game: Game = self.server.current_games_list[game_id][1]
        return game.provide_hint()

    def command_draw(self, client_id: str) -> str:
        if self.server.repo.get_party_id(client_id) == -1:
            return "You are not in a game."
        party_id = self.server.repo.get_party_id(client_id)
        game_id: int = self.server.repo.get_game_id(party_id)
        game: Game = self.server.current_games_list[game_id][1]
        if game.get_current_player().get_id() != int(client_id):
            return "It is not your turn to play"
        already_had_tile: bool = game.game_data.current_hand is not None
        tile = game.draw_tile()
        answer = ""
        if tile is None:
            if getattr(game.game_data, "no_playable_tiles_remaining", False):
                answer = _(
                    "No playable move exists for the remaining tiles. "
                    "The game is over."
                )
            else:
                answer = _("The deck is empty!")
        elif already_had_tile:
            answer = _("You already have a tile in hand.")
        else:
            answer = _("Tile drawn: {tile}").format(tile=tile)
            # Notify other players about the tile draw
            board_message = "OPPONENT_MOVE drew a tile.\n"
            client_username = self.server.repo.get_username(client_id)
            self.server.send_to_group_except(
                party_id,
                board_message,
                client_username,
            )
        return answer

    def command_shuffle(self, client_id: str) -> str:
        if self.server.repo.get_party_id(client_id) == -1:
            return "You are not in a game."
        party_id = self.server.repo.get_party_id(client_id)
        game_id: int = self.server.repo.get_game_id(party_id)
        game: Game = self.server.current_games_list[game_id][1]
        if game.get_current_player().get_id() != int(client_id):
            return "It is not your turn to play"
        seed = game.shuffle_deck()
        return _("Deck shuffled. Algorithm: {algorithm}. Seed: {seed}").format(
            algorithm=game.game_data.shuffle_algo,
            seed=seed,
        )

    def command_save(self, client_id: str, message: str) -> str:
        if self.server.repo.get_party_id(client_id) == -1:
            return "You are not in a game."
        filename = message[5:].strip()
        party_id = self.server.repo.get_party_id(client_id)
        game_id: int = self.server.repo.get_game_id(party_id)
        game: Game = self.server.current_games_list[game_id][1]
        if game.get_current_player().get_id() != int(client_id):
            return "It is not your turn to play"
        if game.save_game_to_file(filename) == 0:
            return _("Game saved to {filename}.").format(filename=filename)
        return _("Failed to save the game to {filename}.").format(
            filename=filename
        )

    def command_load(self, client_id: str, message: str) -> str:
        if self.server.repo.get_party_id(client_id) == -1:
            return "You are not in a game."
        filename = message[5:].strip()
        party_id = self.server.repo.get_party_id(client_id)
        game_id: int = self.server.repo.get_game_id(party_id)
        game: Game = self.server.current_games_list[game_id][1]
        if game.get_current_player().get_id() != int(client_id):
            return "It is not your turn to play"
        if game.load_game_from_file(filename) == 0:
            return _("Game loaded from {filename}.").format(filename=filename)
        return _("Failed to load the game from {filename}.").format(
            filename=filename
        )
