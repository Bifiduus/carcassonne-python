import sqlite3
import threading
from dataclasses import dataclass
from typing import Any

from carcassonne.BusinessLogic.Interfaces.IGamesRepository import IGamesRepository


@dataclass
class GameRepository(IGamesRepository):
    """Repository handling persistence of players, parties and games.

    This class encapsulates all SQL operations so that the server and business
    logic do not need to know about the underlying database.
    """

    db_path: str = "carcassonne.db"

    def __post_init__(self):
        # open sqlite connection once, allow multithreaded access via lock
        self.db = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.Lock()

    def init_database(self):
        rows = self._execute_non_query(
            "CREATE TABLE IF NOT EXISTS groups(group_id, number_of_players, host_player);"
        )
        rows = self._execute_non_query(
            "CREATE TABLE IF NOT EXISTS players(player_id, username, status, group_id, connected);"
        )
        rows = self._execute_non_query(
            "CREATE TABLE IF NOT EXISTS scoreboard(player_id, victories, defeats);"
        )
        rows = self._execute_non_query(
            "CREATE TABLE IF NOT EXISTS current_games(game_id, game_name, group_id);"
        )
        rows = self._execute_non_query(
            "CREATE TABLE IF NOT EXISTS pending_invitations(group_id, invited_player, invitation_status);"
        )

    # low-level helpers
    def _execute_query(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self.lock:
            cur = self.db.cursor()
            cur.execute(query, params)
            return cur.fetchall()

    def _execute_non_query(self, query: str, params: tuple = ()) -> int | None:
        with self.lock:
            cur = self.db.cursor()
            cur.execute(query, params)
            self.db.commit()
            return cur.lastrowid

    # business operations
    def player_exists(self, player_name: str) -> bool:
        rows = self._execute_query(
            "SELECT 1 FROM players WHERE username=?;",
            (player_name,),
        )
        return bool(rows)

    def get_player_profile(self, player_id: int) -> dict[str, Any]:
        rows = self._execute_query(
            "SELECT username, status, victories AS stats_win, defeats AS stats_lose FROM players NATURAL JOIN scoreboard WHERE id=?;",
            (player_id,),
        )
        if not rows:
            return {}
        r = rows[0]
        return {k: r[k] for k in r.keys()}

    def get_username(self, player_id: str) -> str:
        rows = self._execute_query(
            "SELECT username FROM players WHERE player_id=?;",
            (int(player_id),)
        )
        return rows[0][0]

    def change_status(self, client_id: str, status: str) -> str:
        rows = self._execute_non_query(
            "UPDATE players SET status=? WHERE id=?;",
            (status, int(client_id),)
        )
        if rows is None:
            return "Status not changed."
        return f"Status changed to {status}."

    def current_players(self) -> str:
        rows = self._execute_query(
            "SELECT player_id, username, status FROM players WHERE status!='away' AND connected=true;"
        )
        return str([r for r in rows])

    def invitation_received(self, client_id: str):
        rows = self._execute_query(
            "SELECT host_player, group_id FROM pending_invitations NATURAL JOIN groups WHERE invited_player=?;",
            (int(client_id),)
        )
        return rows[0]

    def accept_invitation(self, group_id: int, invited: str):
        self.change_status(invited, "ingame")
        rows = self._execute_non_query(
            "UPDATE players SET group_id=? WHERE player_id=?;",
            (group_id, int(invited),)
        )
        rows = self._execute_non_query(
            "DELETE pending_invitations WHERE invited_player=?;",
            (int(invited),)
        )
        rows = self._execute_non_query(
            "UPDATE groups SET number_of_players=(SELECT number_of_players FROM groups WHERE group_id=?;)+1 WHERE group_id=?;",
            (group_id, group_id)
        )

    def get_game(self, client_id: int):
        rows = self._execute_query(
            "SELECT game_id FROM current_games NATURAL JOIN groups NATURAL JOIN players WHERE player_id=?;",
            (int(client_id),)
        )
        return rows[0]

    # possible to change return type to tuple(int, message)
    def check_all_invitations_resolved(self, client_id: int):
        rows = self._execute_query(
            "SELECT invited_player, username FROM pending_invitations NATURAL JOIN players NATURAL JOIN groups WHERE invitation_status!='waiting' AND host_player=?;",
            (client_id,)
        )
        if not rows:
            return True
        return False

    def get_scoreboard(self) -> str:
        rows = self._execute_query(
            "SELECT player_id AS id, username, victories, defeats, (victories + defeats) AS total_games FROM scoreboard NATURAL JOIN players;"
        )
        return str([r for r in rows])

    def invitation_sent_from(self, client_id: str) -> bool:
        rows = self._execute_query(
            "SELECT 1 FROM pending_invitations NATURAL JOIN groups WHERE host_player=? AND invitation_status!='accepted';",
            (int(client_id),)
        )
        return bool(rows)

    def cancel_invitation_from(self, client_id: str, players: list[str]):
        if players is []:
            rows = self._execute_non_query(
                "DELETE FROM pending_invitations NATURAL JOIN groups WHERE host_player=? AND invitation_status=='waiting';",
                (int(client_id),)
            )
            if bool(rows):
                return "All invitations cancelled."
            return ""
        for player_username in players:
            rows = self._execute_non_query(
                "DELETE FROM pending_invitations NATURAL JOIN groups NATURAL JOIN players WHERE host_player=? AND invitation_status=='waiting' AND username=?;",
                (int(client_id), player_username)
            )
        return "Your invitation(s) have been cancelled."

    def create_party(self, name: str, player_names: list[str], host_id: int) -> int | None:
        party_id = self._execute_non_query(
            "INSERT INTO groups(number_of_players, host_player) VALUES (?, ?);",
            (1, host_id,),
        )
        for username in player_names:
            player_id: int = self._execute_query(
                "SELECT player_id FROM player WHERE username=?;",
                (username,)
            )[0][0]
            self._execute_non_query(
                "INSERT INTO party_players(party_id, player_id, accepted) VALUES (?, ?, ?);",
                (party_id, player_id, "pending"),
            )
        return party_id

    def get_party(self, host_id) -> list[str]:
        rows = self._execute_query(
            "SELECT username FROM party_players NATURAL JOIN parties NATURAL JOIN players WHERE host_id=?;",
            (host_id,)
        )
        return [r[0] for r in rows]

    def get_party_name(self, host_id: int) -> str:
        rows = self._execute_query(
            "SELECT party_name FROM parties WHERE host_id=?;",
            (host_id,)
        )
        return rows[0][0]

    def send_invitation(self, invited_player: str, invitee_player: str) -> bool:
        group_id: int = self._execute_query(
            "SELECT group_id FROM groups WHERE host_player=?;",
            (int(invitee_player),)
        )[0][0]
        rows = self._execute_non_query(
            "INSERT INTO pending_invitations(group_id, invited_player, invitation_status) VALUES(?, ?, ?);",
            (group_id, int(invited_player), "waiting")
        )
        return bool(rows)

    def close(self):
        try:
            self.db.close()
        except Exception:
            pass
