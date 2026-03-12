import sqlite3
import threading
from dataclasses import dataclass
from typing import List, Optional, Any


@dataclass
class GameRepository:
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
            "SELECT username, status, score, stats_win, stats_lose "
            "FROM players WHERE id=?;",
            (player_id,),
        )
        if not rows:
            return {}
        r = rows[0]
        return {k: r[k] for k in r.keys()}

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
            "SELECT player_id, username, status FROM players WHERE status!='away';"
        )
        return str([r for r in rows])

    def invitation_received(self, client_id: str):
        rows = self._execute_query(
            "SELECT host_player, party_id FROM pending_invitations WHERE invited_player=?;",
            (int(client_id),)
        )
        return rows[0]

    def accept_invitation(self, party_id: int, invited: str):
        self.change_status(invited, "ingame")
        rows = self._execute_non_query(
            "UPDATE party_players SET accepted='accepted' WHERE player_id=? AND party_id=?;",
            (int(invited), party_id)
        )

    def get_game(self, client_id: int):
        rows = self._execute_query(
            "SELECT game_id FROM current_parties WHERE player_id=?;",
            (int(client_id),)
        )
        return rows[0]

    # possible to change return type to tuple(int, message)
    def check_all_invitations_resolved(self, client_id: int):
        rows = self._execute_query(
            "SELECT player_id, username FROM pending_invitations WHERE accepted!='accepted' AND host_player=?;",
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
            "SELECT 1 FROM pending_invitations WHERE host_player=? AND accepted!='accepted';",
            (int(client_id),)
        )
        return bool(rows)

    def cancel_invitation_from(self, client_id: str):
        rows = self._execute_non_query(
            "DELETE FROM pending_invitations WHERE host_player=?;",
            (int(client_id),)
        )
        if bool(rows):
            return "Invitation cancelled."
        return ""

    def create_party(self, name: str, player_names: List[str], host_id: int) -> int | None:
        party_id = self._execute_non_query(
            "INSERT INTO parties(party_name, host_id) VALUES (?, ?);",
            (name, host_id,),
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

    def close(self):
        try:
            self.db.close()
        except Exception:
            pass
