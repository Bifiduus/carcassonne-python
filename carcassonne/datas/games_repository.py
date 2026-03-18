import sqlite3
import threading
from dataclasses import dataclass
import time
from typing import Any

from carcassonne.business_logic.interfaces.i_games_repository import IGamesRepository


@dataclass
class GameRepository(IGamesRepository):
    """Repository handling persistence of players, parties and games.

    This class encapsulates all SQL operations so that the server and business
    logic do not need to know about the underlying database.
    """

    db_path: str = "carcassonne.db"

    def __init__(self):
        self.closed = False
        self.__post_init__()
        self.init_database()

    def __post_init__(self):
        # open sqlite connection once, allow multithreaded access via lock
        self.db = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.Lock()

    def init_database(self):
        table_players = "CREATE TABLE IF NOT EXISTS players(player_id INTEGER CONSTRAINT player_id_c PRIMARY KEY AUTOINCREMENT,"
        table_players += " username varchar(30) CONSTRAINT username_constraint NOT NULL,"
        table_players += f" status varchar(10) CONSTRAINT player_status CHECK(status IN (\"idle\",\"ingame\", \"away\",\"waitgame\")),"
        # can be null ? group_id
        table_players += " group_id INTEGER CONSTRAINT group_id_c REFERENCES groups(group_id),"
        table_players += " connected boolean);"
        rows = self._execute_non_query(table_players)

        table_groups = "CREATE TABLE IF NOT EXISTS groups(group_id int CONSTRAINT group_id_c PRIMARY KEY,"
        table_groups += " number_of_players int CONSTRAINT number_of_players CHECK(number_of_players >= 0),"
        table_groups += "host_player int CONSTRAINT host_player REFERENCES players(player_id));"
        rows = self._execute_non_query(table_groups)

        table_scoreboard = "CREATE TABLE IF NOT EXISTS scoreboard(player_id int CONSTRAINT player_id_scoreboard REFERENCES players(player_id),"
        table_scoreboard += " victories int CONSTRAINT victories CHECK(victories >= 0),"
        table_scoreboard += " defeats int CONSTRAINT defeats CHECK(defeats >= 0));"
        rows = self._execute_non_query(table_scoreboard)

        table_games = "CREATE TABLE IF NOT EXISTS current_games(game_id int CONSTRAINT game_id PRIMARY KEY,"
        table_games += " game_name varchar(30) CONSTRAINT game_name NOT NULL,"
        table_games += " group_id int CONSTRAINT group_id_game REFERENCES groups(group_id));"
        rows = self._execute_non_query(table_games)

        table_invitations = "CREATE TABLE IF NOT EXISTS pending_invitations(invitation_id int CONSTRAINT invitation_id PRIMARY KEY,"
        table_invitations += " group_id int CONSTRAINT group_id_invitation REFERENCES groups(group_id),"
        table_invitations += " invited_player int CONSTRAINT invited_player REFERENCES players(player_id),"
        table_invitations += f" invitation_status varchar(20) CONSTRAINT invitation_status CHECK(invitation_status IN (\"waiting\",\"accepted\")),"
        table_invitations += " sending_time float CONSTRAINT sending_time NOT NULL);"
        rows = self._execute_non_query(table_invitations)

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

    def get_next_available_id(self) -> int:
        rows = self._execute_query(
            "SELECT * FROM players;"
        )
        return len(rows) + 1

    def is_accounted_for(self):
        rows = self._execute_query(
            "SELECT 1 FROM players;"
        )
        return len(rows) >= 1

    def create_online_player(self, username: str) -> str:
        if len(username) <= 30:
            rows = self._execute_non_query(
                "INSERT INTO players(username, status, connected) VALUES(?, ?, ?);",
                (username, "idle", True)
            )
            player_id: int = self.get_id_from_username(username)
            rows = self._execute_non_query(
                "INSERT INTO scoreboard(player_id, victories, defeats) VALUES(?, 0, 0);",
                (player_id,)
            )
            return "Account successfully created."
        else:
            return "Error creating the account, username too long (max 30 characters)."

    def get_online_player(self) -> str:
        rows = self._execute_query(
            "SELECT username FROM players;"
        )
        return rows[0][0]

    def player_exists(self, player_name: str) -> bool:
        rows = self._execute_query(
            "SELECT 1 FROM players WHERE username=?;",
            (player_name,),
        )
        return bool(rows)

    def get_player_profile(self, player_id: int) -> dict[str, Any]:
        rows = self._execute_query(
            "SELECT username, status, victories AS stats_win, defeats AS stats_lose FROM players NATURAL JOIN scoreboard WHERE player_id=?;",
            (player_id,),
        )
        if not rows:
            return {}
        r = rows[0]
        score = self.get_score(r['stats_win'], r['stats_lose'])
        profile: dict = {k: r[k] for k in r.keys()}
        profile['score'] = score
        return profile

    def get_score(self, wins: int, loses: int):
        return (wins - loses) % 10

    def get_username(self, player_id: str) -> str:
        rows = self._execute_query(
            "SELECT username FROM players WHERE player_id=?;",
            (int(player_id),)
        )
        return rows[0][0]

    def get_id_from_username(self, player_username: str) -> int:
        rows = self._execute_query(
            "SELECT player_id FROM players WHERE username=?;",
            (player_username,)
        )
        return rows[0][0]

    def change_status(self, client_username: str, status: str) -> str:
        client_id = self.get_id_from_username(client_username)
        rows = self._execute_non_query(
            "UPDATE players SET status=? WHERE player_id=?;",
            (status, client_id,)
        )
        if rows is None:
            return "Status not changed."
        return f"Status changed to {status}."

    def current_players(self) -> str:
        rows = self._execute_query(
            "SELECT player_id, username, status FROM players WHERE status!='away' AND connected=True;"
        )
        answer = ([(r['player_id'], r['username'], r['status']) for r in rows])
        return f"List of current players: {answer}"

    def invitation_received(self, client_username: str):
        client_id: int = self._execute_query(
            "SELECT player_id FROM players WHERE username=?;",
            (client_username,)
        )[0][0]
        rows = self._execute_query(
            "SELECT host_player, group_id FROM pending_invitations NATURAL JOIN groups WHERE invited_player=?;",
            (client_id,)
        )
        return rows[0]

    def accept_invitation(self, group_id: int, invited: str):
        invited_id = self.get_id_from_username(invited)
        self.change_status(str(invited_id), "ingame")
        rows = self._execute_non_query(
            "UPDATE players SET group_id=? WHERE player_id=?;",
            (group_id, int(invited_id),)
        )
        rows = self._execute_non_query(
            "DELETE pending_invitations WHERE invited_player=?;",
            (int(invited),)
        )
        rows = self._execute_non_query(
            "UPDATE groups SET number_of_players=(SELECT number_of_players FROM groups WHERE group_id=?;)+1 WHERE group_id=?;",
            (group_id, group_id)
        )

    def get_game(self, client_id: str):
        rows = self._execute_query(
            "SELECT game_id FROM current_games NATURAL JOIN groups NATURAL JOIN players WHERE player_id=?;",
            (int(client_id),)
        )
        return rows[0]

    # possible to change return type to tuple(int, message)
    def check_all_invitations_resolved(self, client_id: str):
        rows = self._execute_query(
            "SELECT invited_player, username FROM pending_invitations NATURAL JOIN players NATURAL JOIN groups WHERE host_id=?;",
            (int(client_id),)
        )
        if not rows:
            return True
        return False

    def get_scoreboard(self) -> list[sqlite3.Row]:
        rows = self._execute_query(
            "SELECT player_id AS id, username, victories, defeats, (victories + defeats) AS total_games FROM scoreboard NATURAL JOIN players;"
        )
        return rows

    def invitation_sent_from(self, client_username: str) -> bool:
        client_id: int = self.get_id_from_username(client_username)
        rows = self._execute_query(
            "SELECT 1 FROM pending_invitations NATURAL JOIN groups WHERE host_player=? AND invitation_status!='accepted';",
            (client_id,)
        )
        return bool(rows)

    def cancel_invitation_from(self, client_username: str, players: list[str]):
        client_id = self.get_id_from_username(client_username)
        if players is []:
            rows = self._execute_non_query(
                "DELETE FROM pending_invitations NATURAL JOIN groups WHERE host_player=? AND invitation_status=='waiting';",
                (client_id,)
            )
            if bool(rows):
                return "All invitations cancelled."
            return ""
        for player_username in players:
            rows = self._execute_non_query(
                "DELETE FROM pending_invitations NATURAL JOIN groups NATURAL JOIN players WHERE host_player=? AND invitation_status=='waiting' AND username=?;",
                (client_id, player_username)
            )
        return "Your invitation(s) have been cancelled."

    def check_all_invitations_timeout(self, timeout):
        rows = self._execute_query(
            "SELECT invitation_id, sending_time FROM pending_invitations;"
        )
        for row in rows:
            id, t = row
            if time.time() - t < timeout:
                self.cancel_invitation(id)

    def cancel_invitation(self, invitation_id) -> bool:
        rows = self._execute_non_query(
            "DELETE FORM pending_invitations WHERE invitation_id=?;",
            (invitation_id,)
        )
        return bool(rows)

    def create_party(self, name: str, player_names: list[str], client_username: str) -> int | None:
        rows = self._execute_query(
            "SELECT player_id FROM players WHERE username=?;",
            (client_username,)
        )
        if len(rows) == 0:
            print("Error: no such username.")
            return
        host_id: int = rows[0][0]
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

    def get_party(self, client_id: str) -> list[str]:
        rows = self._execute_query(
            "SELECT player_id FROM groups NATURAL JOIN players WHERE host_id=?;",
            (client_id,)
        )
        return [r[0] for r in rows]  # possibly int

    def get_party_name(self, client_id: str) -> str:
        rows = self._execute_query(
            "SELECT party_name FROM parties WHERE host_id=?;",
            (int(client_id),)
        )
        return rows[0][0]

    def send_invitation(self, invited_player: str, invitee_player: str) -> bool:
        invitee_id: int = self._execute_query(
            "SELECT player_id FROM players WHERE username=?;",
            (invitee_player,)
        )[0][0]
        group_id: int = self._execute_query(
            "SELECT group_id FROM groups WHERE host_player=?;",
            (invitee_player,)
        )[0][0]
        rows = self._execute_non_query(
            "INSERT INTO pending_invitations(group_id, invited_player, invitation_status, sending_time) VALUES(?, ?, ?);",
            (group_id, int(invited_player), "waiting", time.time())
        )
        return bool(rows)

    def close(self):
        try:
            self.db.close()
            self.closed = True
        except Exception:
            pass

    def reopen(self):
        self.__post_init__()
        self.closed = False

    def is_database_closed(self):
        return self.closed
