import sqlite3
import threading
from dataclasses import dataclass
import time
from typing import Any

from carcassonne.business_logic.interfaces.i_games_repository\
    import IGamesRepository


@dataclass
class GameRepository(IGamesRepository):
    """Repository handling persistence of players, parties and games.

    This class encapsulates all SQL operations so that the server and business
    logic do not need to know about the underlying database.
    """

    db_path: str = "carcassonne/datas/carcassonne.db"

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
        table_players = "CREATE TABLE IF NOT EXISTS players"\
            "(player_id INTEGER CONSTRAINT player_id_c" \
            " PRIMARY KEY AUTOINCREMENT,"
        table_players += " username varchar(30) CONSTRAINT"\
            " username_constraint NOT NULL,"
        table_players += " status varchar(10) CONSTRAINT player_status"\
            " CHECK(status IN (\"idle\",\"ingame\", \"away\",\"waitgame\")),"
        table_players += " group_id INTEGER CONSTRAINT group_id_c"\
            " REFERENCES groups(group_id),"
        table_players += " password varchar(20) CONSTRAINT password NOT NULL,"
        table_players += " connected boolean);"
        self._execute_non_query(table_players)

        table_groups = "CREATE TABLE IF NOT EXISTS groups"\
            "(group_id INTEGER CONSTRAINT group_id_c PRIMARY KEY"\
            " AUTOINCREMENT,"
        table_groups += " number_of_players int CONSTRAINT"\
            " number_of_players CHECK(number_of_players >= 0),"
        table_groups += "host_player int CONSTRAINT host_player"\
            " REFERENCES players(player_id));"
        self._execute_non_query(table_groups)

        table_scoreboard = "CREATE TABLE IF NOT EXISTS scoreboard"\
            "(player_id int CONSTRAINT player_id_scoreboard REFERENCES"\
            " players(player_id),"
        table_scoreboard += " victories int CONSTRAINT victories"\
            " CHECK(victories >= 0),"
        table_scoreboard += " defeats int CONSTRAINT defeats"\
            " CHECK(defeats >= 0));"
        self._execute_non_query(table_scoreboard)

        table_games = "CREATE TABLE IF NOT EXISTS current_games"\
            "(game_id INTEGER CONSTRAINT game_id PRIMARY KEY AUTOINCREMENT,"
        table_games += " game_name varchar(30) CONSTRAINT"\
            " game_name NOT NULL,"
        table_games += " group_id int CONSTRAINT group_id_game"\
            " REFERENCES groups(group_id));"
        self._execute_non_query(table_games)

        table_invitations = "CREATE TABLE IF NOT EXISTS pending_invitations"\
            "(invitation_id INTEGER CONSTRAINT invitation_id "\
            "PRIMARY KEY AUTOINCREMENT,"
        table_invitations += " group_id int CONSTRAINT group_id_invitation"\
            " REFERENCES groups(group_id),"
        table_invitations += " invited_player int CONSTRAINT invited_player"\
            " REFERENCES players(player_id),"
        table_invitations += " invitation_status varchar(20) CONSTRAINT"\
            " invitation_status CHECK(invitation_status"\
            " IN (\"waiting\",\"accepted\")),"
        table_invitations += " sending_time float CONSTRAINT sending_time"\
            " NOT NULL);"
        self._execute_non_query(table_invitations)

        usernames_table = "CREATE TABLE IF NOT EXISTS usernames(server "\
            "varchar(30) CONSTRAINT server PRIMARY KEY,"
        usernames_table += "username varchar(30) CONSTRAINT usernames_table"\
            " NOT NULL);"
        self._execute_non_query(usernames_table)

        usernames_table = "CREATE TABLE IF NOT EXISTS usernames(server "\
            "varchar(30) CONSTRAINT server PRIMARY KEY,"
        usernames_table += "username varchar(30) CONSTRAINT usernames_table"\
            " NOT NULL);"
        self._execute_non_query(usernames_table)

    # low-level helpers
    def _execute_query(self, query: str,
                       params: tuple = ()) -> list[sqlite3.Row]:
        with self.lock:
            cur = self.db.cursor()
            cur.execute(query, params)
            return cur.fetchall()

    def _execute_non_query(self, query: str,
                           params: tuple = ()) -> int | None:
        with self.lock:
            cur = self.db.cursor()
            cur.execute(query, params)
            self.db.commit()
            return cur.lastrowid

    # business operations

    def get_next_available_id(self) -> int:
        rows = self._execute_query(
            "SELECT player_id FROM players ORDER BY player_id DESC LIMIT 1;"
        )
        return rows[0]['player_id'] + 1

    def is_accounted_for(self):
        rows = self._execute_query(
            "SELECT 1 FROM players;"
        )
        return len(rows) >= 1

    def create_default_online_player(self, username: str, password: str,
                                     server: str) -> str:
        if 3 <= len(username) <= 30:
            self._execute_non_query(
                "INSERT INTO players(username, status, password, connected)"
                " VALUES(?, ?, ?, ?);",
                (username, "idle", password, False)
            )
            player_id: int = self.get_id_from_username(username)
            self._execute_non_query(
                "INSERT INTO scoreboard(player_id, victories, defeats)"
                " VALUES(?, 0, 0);",
                (player_id,)
            )
            self._execute_non_query(
                "INSERT INTO usernames(server, username) VALUES(?, ?);",
                (server, username)
            )
            return "Account successfully created."
        else:
            return "Error creating the account, username too long" \
                " (max 30 characters)."

    def set_new_username_for_server(self, server: str, username: str):
        self._execute_non_query(
            "INSERT INTO usernames(server, username) VALUES(?, ?);",
            (server, username)
        )

    def get_online_player(self, server: str) -> str:
        rows = self._execute_query(
            "SELECT username FROM usernames WHERE server=?;",
            (server,)
        )
        return rows[0]['username']

    def has_no_special_username(self, server: str) -> bool:
        rows = self._execute_query(
            "SELECT username FROM usernames WHERE server=?",
            (server,)
        )
        return not bool(rows)

    def player_exists(self, player_name: str) -> bool:
        rows = self._execute_query(
            "SELECT 1 FROM players WHERE username=?;",
            (player_name,),
        )
        return bool(rows)

    def registering(self, username: str, password: str):
        if self.player_exists(username):
            rows = self._execute_query(
                "SELECT password, connected FROM players WHERE username=?;",
                (username,)
            )
            real_password: str = rows[0]['password']
            connected: bool = rows[0]['connected']
            if real_password == password and not connected:
                self._execute_non_query(
                    "UPDATE players SET connected=? WHERE username=?;",
                    (True, username)
                )
                return True
            return False
        else:
            rows_players = self._execute_non_query(
                "INSERT INTO players(username, status, password, connected)"
                " VALUES(?, ?, ?, ?);",
                (username, "idle", password, True)
            )
            player_id: int = self.get_id_from_username(username)
            rows_scoreboard = self._execute_non_query(
                "INSERT INTO scoreboard(player_id, victories, defeats)"
                " VALUES(?, 0, 0);",
                (player_id,)
            )
            if bool(rows_players) and bool(rows_scoreboard):
                return True
            return False

    def get_password(self, player_id: int) -> str:
        rows = self._execute_query(
            "SELECT password FROM players WHERE player_id=?;",
            (player_id,)
        )
        return rows[0][0]

    def get_player_profile(self, player_id: int) -> dict[str, Any]:
        rows = self._execute_query(
            "SELECT username, status, victories AS stats_win, defeats AS"
            " stats_lose FROM players NATURAL JOIN scoreboard"
            " WHERE player_id=?;",
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

    def get_group(self, host_id: int) -> int:
        rows = self._execute_query(
            "SELECT group_id FROM groups WHERE host_player=?;",
            (host_id,)
        )
        return rows[0]['group_id']

    def party_is_launched(self, host_id: int) -> bool:
        group_id = self.get_group(host_id)
        rows = self._execute_query(
            "SELECT game_id FROM current_games WHERE group_id=?;",
            (group_id,)
        )
        return bool(rows)

    def get_id_from_username(self, player_username: str) -> int:
        rows = self._execute_query(
            "SELECT player_id FROM players WHERE username=?;",
            (player_username,)
        )
        if not bool(rows):
            return -1
        return rows[0][0]

    def change_status(self, client_id: str, status: str) -> str:
        rows = self._execute_non_query(
            "UPDATE players SET status=? WHERE player_id=?;",
            (status, int(client_id),)
        )
        if rows is None:
            return "Status not changed."
        return f"Status changed to {status}."

    def current_players(self) -> str:
        rows = self._execute_query(
            "SELECT player_id, username, status FROM players"
            " WHERE status!='away' AND connected=True;"
        )
        answer = ([(r['player_id'], r['username'], r['status']) for r in rows])
        return f"List of current players: {answer}"

    def invitation_received(self, client_id: str) -> tuple[int, int]:
        rows = self._execute_query(
            "SELECT host_player, group_id FROM pending_invitations"
            " NATURAL JOIN groups WHERE invited_player=?;",
            (int(client_id),)
        )
        if rows == []:
            return (-1, -1)
        return rows[0]['host_player'], rows[0]['group_id']

    def has_been_invited(self, invited: str) -> bool:
        rows = self._execute_query(
            "SELECT invitation_id FROM pending_invitations WHERE invited_player=?;",
            (int(invited),)
        )
        return bool(rows)

    def accept_invitation(self, group_id: int, invited: str):
        if not self.has_been_invited(invited):
            return
        self.change_status(invited, "waitgame")
        self._execute_non_query(
            "UPDATE players SET group_id=? WHERE player_id=?;",
            (group_id, int(invited),)
        )
        rows = self._execute_non_query(
            "DELETE FROM pending_invitations WHERE invited_player=?;",
            (int(invited),)
        )
        rows = self._execute_query(
            "SELECT number_of_players FROM groups WHERE group_id=?;",
            (group_id,)
        )
        rows = self._execute_non_query(
            "UPDATE groups SET number_of_players=?+1 WHERE group_id=?;",
            (rows[0][0], group_id)
        )

    def reject_invitation(self, invited: str):
        self._execute_non_query(
            "DELETE FROM pending_invitations WHERE invited_player=?;",
            (int(invited),)
        )

    def get_game(self, client_id: str) -> int:
        rows = self._execute_query(
            "SELECT game_id FROM current_games NATURAL JOIN groups"
            " NATURAL JOIN players WHERE player_id=?;",
            (int(client_id),)
        )
        return rows[0][0]

    def get_game_id(self, group_id: int) -> int:
        rows = self._execute_query(
            "SELECT * FROM current_games;"
        )
        rows = self._execute_query(
            "SELECT game_id FROM current_games WHERE group_id=?;",
            (group_id,)
        )
        return rows[0]['game_id']

    # possible to change return type to tuple(int, message)
    def check_all_invitations_resolved(self, client_id: str):
        rows = self._execute_query(
            "SELECT invited_player, username, invitation_status FROM"
            " pending_invitations"
            " NATURAL JOIN players NATURAL JOIN groups WHERE host_player=?;",
            (int(client_id),)
        )
        if not rows:
            return True
        for row in rows:
            if row['invitation_status'] == 'waiting':
                return False
        return True

    def get_host_from_party(self, party_id: int) -> int:
        rows = self._execute_query(
            "SELECT host_player FROM groups WHERE group_id=?;",
            (party_id,)
        )
        return rows[0]['host_player']

    def get_scoreboard(self) -> list[sqlite3.Row]:
        rows = self._execute_query(
            "SELECT player_id AS id, username, victories, defeats,"
            " (victories + defeats) AS total_games FROM scoreboard"
            " NATURAL JOIN players;"
        )
        return rows

    def invitation_sent_from(self, client_id: str) -> bool:
        group_id = self.get_group(int(client_id))
        rows = self._execute_query(
            "SELECT invitation_id FROM pending_invitations "
            " WHERE group_id=? AND invitation_status!='accepted';",
            (group_id,)
        )
        return bool(rows)

    def cancel_invitation_from(self, client_id: str, players: list[str]):
        if players == []:
            rows = self._execute_query(
                "SELECT group_id FROM groups WHERE host_player=?;",
                (client_id,)
            )
            group_id: int = rows[0]['group_id']
            rows = self._execute_non_query(
                "DELETE FROM pending_invitations WHERE group_id=?;",
                (group_id,)
            )
            if bool(rows):
                return "All invitations cancelled."
            return ""
        for player_id in players:
            rows = self._execute_non_query(
                "DELETE FROM pending_invitations WHERE invited_player=?;",
                (int(player_id),)
            )
        return "Your invitation(s) have been cancelled."

    def check_all_invitations_timeout(self, timeout) -> list[int]:
        rows = self._execute_query(
            "SELECT invitation_id, sending_time, invited_player FROM pending_invitations;"
        )
        timed_out = []
        for row in rows:
            id, t, invited = row
            if time.time() - t > timeout:
                timed_out.append(invited)
                self.cancel_invitation(id)
        return timed_out

    def cancel_invitation(self, invitation_id: int) -> bool:
        rows = self._execute_non_query(
            "DELETE FROM pending_invitations WHERE invitation_id=?;",
            (invitation_id,)
        )
        return bool(rows)

    def get_parties(self) -> list[int]:
        rows = self._execute_query(
            "SELECT group_id FROM groups;"
        )
        parties: list[int] = []
        for row in rows:
            parties.append(row['group_id'])
        return parties

    def create_party(self, client_username: str) -> int | None:
        host_id: int = self.get_id_from_username(client_username)
        self.change_status(str(host_id), "waitgame")
        self._execute_non_query(
            "INSERT INTO groups(number_of_players, host_player)"
            " VALUES (?, ?);",
            (1, host_id,),
        )
        rows = self._execute_query(
            "SELECT group_id FROM groups WHERE host_player=?;",
            (host_id,)
        )
        self._execute_non_query(
            "UPDATE players SET group_id=? WHERE player_id=?;",
            (rows[0]['group_id'], host_id)
        )
        rows = self._execute_query(
            "SELECT group_id FROM groups WHERE host_player=?;",
            (host_id,)
        )
        party_id: int = rows[0]['group_id']
        return party_id

    def get_party(self, client_id: str) -> list[int]:
        rows = self._execute_query(
            "SELECT player_id FROM groups NATURAL JOIN players"
            " WHERE host_player=?;",
            (int(client_id),)
        )
        return [r[0] for r in rows]

    def clean_party(self, party: int):
        check = self.clean_party_players(party)
        if not check:
            print("Error cleaning the party's players !")
            return
        self._execute_non_query(
            "DELETE FROM current_games WHERE group_id=?;",
            (party,)
        )
        self._execute_non_query(
            "DELETE FROM groups WHERE group_id=?;",
            (party,)
        )

    def client_quit(self, client_username: str):
        self._execute_non_query(
            "UPDATE players SET connected=?, group_id=?, status=? WHERE username=?;",
            (False, None, client_username, "idle")
        )

    def check_party_is_alive(self, group_id: int) -> bool:
        rows = self._execute_query(
            "SELECT player_id FROM players WHERE group_id=?;",
            (group_id,)
        )
        if len(rows) > 0:
            return True
        return False

    def get_group_from_game(self, game_id: int) -> int:
        rows = self._execute_query(
            "SELECT group_id FROM current_games WHERE game_id=?;",
            (game_id,)
        )
        return rows[0]['group_id']

    def clean_party_players(self, party: int) -> bool:
        rows = self._execute_non_query(
            "UPDATE players SET group_id=?, status=? WHERE group_id=?;",
            (None, 'idle', party)
        )
        return bool(rows)

    def get_party_id(self, client_id: str) -> int:
        rows = self._execute_query(
            "SELECT group_id FROM players WHERE player_id=?;",
            (int(client_id),)
        )
        if bool(rows):
            return rows[0]['group_id']
        return -1

    def create_game(self, game_name: str, group_id: int):
        rows = self._execute_non_query(
            "INSERT INTO current_games(game_name, group_id)"
            " VALUES(?, ?);",
            (game_name, group_id)
        )

    def send_invitation(self, invited_player: str,
                        invitee_player: str) -> bool:
        group_id: int = self._execute_query(
            "SELECT group_id FROM groups WHERE host_player=?;",
            (int(invitee_player),)
        )[0][0]
        rows = self._execute_query(
            "SELECT status FROM players WHERE player_id=?;",
            (int(invited_player),)
        )
        status = rows[0]['status']
        if status in ["idle", 'waitgame']:
            rows = self._execute_non_query(
                "INSERT INTO pending_invitations(group_id, invited_player,"
                " invitation_status, sending_time) VALUES(?, ?, ?, ?);",
                (group_id, int(invited_player), "waiting", time.time())
            )
            return bool(rows)
        return False

    def get_players_from_group(self, group_id: int) -> list[str]:
        rows = self._execute_query(
            "SELECT username FROM players WHERE group_id=?;",
            (group_id,)
        )
        players: list[str] = []
        if len(rows) <= 1:
            return players
        for row in rows:
            players.append(row['username'])
        return players

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
