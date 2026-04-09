import sys
import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path
import time
from typing import Any

from carcassonne.interfaces.i_games_repository import (
    IGamesRepository,
)
from carcassonne.i18n import gettext as _


@dataclass
class GameRepository(IGamesRepository):
    """Repository handling persistence of players, parties and games.

    This class encapsulates all SQL operations so that the server and business
    logic do not need to know about the underlying database.
    """

    db_path: str = str(Path.home() / ".carcassonne" / "carcassonne.db")

    def __init__(self):
        self.closed = False
        self.__post_init__()
        self.init_database()

    def __post_init__(self):
        # open sqlite connection once, allow multithreaded access via lock
        db_path = Path(self.db_path).expanduser()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db_path = str(db_path)
        self.db = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.lock = threading.Lock()

    def init_database(self):
        """Initialize database for a fresh data state."""
        table_players = (
            "CREATE TABLE IF NOT EXISTS players"
            "(player_id INTEGER CONSTRAINT player_id_c"
            " PRIMARY KEY AUTOINCREMENT,"
        )
        table_players += (
            " username varchar(30) CONSTRAINT" " username_constraint NOT NULL,"
        )
        table_players += (
            " status varchar(10) CONSTRAINT player_status"
            ' CHECK(status IN ("idle","ingame", "away","waitgame")),'
        )
        table_players += (
            " group_id INTEGER CONSTRAINT group_id_c"
            " REFERENCES groups(group_id),"
        )
        table_players += " password varchar(20) CONSTRAINT password NOT NULL,"
        table_players += " connected boolean, proper_client boolean);"
        self._execute_non_query(table_players)

        table_groups = (
            "CREATE TABLE IF NOT EXISTS groups"
            "(group_id INTEGER CONSTRAINT group_id_c PRIMARY KEY"
            " AUTOINCREMENT,"
        )
        table_groups += (
            " number_of_players int CONSTRAINT"
            " number_of_players CHECK(number_of_players >= 0),"
        )
        table_groups += (
            "host_player int CONSTRAINT host_player"
            " REFERENCES players(player_id));"
        )
        self._execute_non_query(table_groups)

        table_scoreboard = (
            "CREATE TABLE IF NOT EXISTS scoreboard"
            "(player_id int CONSTRAINT player_id_scoreboard REFERENCES"
            " players(player_id),"
        )
        table_scoreboard += (
            " victories int CONSTRAINT victories" " CHECK(victories >= 0),"
        )
        table_scoreboard += (
            " defeats int CONSTRAINT defeats" " CHECK(defeats >= 0));"
        )
        self._execute_non_query(table_scoreboard)

        table_games = (
            "CREATE TABLE IF NOT EXISTS current_games"
            "(game_id INTEGER CONSTRAINT game_id PRIMARY KEY AUTOINCREMENT,"
        )
        table_games += (
            " game_name varchar(30) CONSTRAINT" " game_name NOT NULL,"
        )
        table_games += (
            " group_id int CONSTRAINT group_id_game"
            " REFERENCES groups(group_id));"
        )
        self._execute_non_query(table_games)

        table_invitations = (
            "CREATE TABLE IF NOT EXISTS pending_invitations"
            "(invitation_id INTEGER CONSTRAINT invitation_id "
            "PRIMARY KEY AUTOINCREMENT,"
        )
        table_invitations += (
            " group_id int CONSTRAINT group_id_invitation"
            " REFERENCES groups(group_id),"
        )
        table_invitations += (
            " invited_player int CONSTRAINT invited_player"
            " REFERENCES players(player_id),"
        )
        table_invitations += (
            " invitation_status varchar(20) CONSTRAINT"
            " invitation_status CHECK(invitation_status"
            ' IN ("waiting","accepted")),'
        )
        table_invitations += (
            " sending_time float CONSTRAINT sending_time" " NOT NULL);"
        )
        self._execute_non_query(table_invitations)

        usernames_table = (
            "CREATE TABLE IF NOT EXISTS usernames(server "
            "varchar(30) CONSTRAINT server PRIMARY KEY,"
        )
        usernames_table += (
            "username varchar(30) CONSTRAINT usernames_table" " NOT NULL);"
        )
        self._execute_non_query(usernames_table)

        timeout_table = "CREATE TABLE IF NOT EXISTS timeouts(player_id int" \
            " CONSTRAINT player_id_timeouts REFERENCES" \
            " players(player_id), timeout_end float CONSTRAINT" \
            " timeout_end NOT NULL);"
        self._execute_non_query(timeout_table)

    # low-level helpers
    def _execute_query(
        self, query: str, params: tuple = ()
    ) -> list[sqlite3.Row]:
        """Execute the  execute query operation on data state.

        Args:
            query: SQL query string executed against the repository database.
            params: SQL parameters bound to placeholders in the query.

        Returns:
            list[sqlite3.Row]: Rows fetched after executing the SQL query.
        """
        with self.lock:
            cur = self.db.cursor()
            cur.execute(query, params)
            return cur.fetchall()

    def _execute_non_query(self, query: str, params: tuple = ()) -> int | None:
        """Execute the execute non query operation on data state.

        Args:
            query: SQL query string executed against the repository database.
            params: SQL parameters bound to placeholders in the query.

        Returns:
            int | None: The last row ID of the executed non-query,
                or None when not applicable.
        """
        with self.lock:
            cur = self.db.cursor()
            cur.execute(query, params)
            self.db.commit()
            return cur.lastrowid

    # business operations

    def get_next_available_id(self) -> int:
        """Return the next available id from repository data or in-memory state.

        Returns:
            int: Player identifier immediately after the current maximum id.
        """
        rows = self._execute_query(
            "SELECT player_id FROM players ORDER BY player_id DESC LIMIT 1;"
        )
        return rows[0]["player_id"] + 1

    def is_accounted_for(self):
        """Check whether accounted for is true in the current state.

        Returns:
            bool: True when at least one player account exists in the database.
        """
        rows = self._execute_query("SELECT 1 FROM players;")
        return len(rows) >= 1

    def set_game_end_score(self, game_id: int, winner: int):
        """Update the game end score value in the underlying data structure.

        Args:
            game_id: Identifier of the persisted game targeted.
            winner: Winner value handled.

        Returns:
            None.
        """
        if winner < 0:
            return
        self._execute_non_query(
            "UPDATE scoreboard SET victories=victories+1 WHERE player_id=?;",
            (winner,),
        )
        current_group = self.get_group_from_game(game_id)
        losers = self.get_players_from_group(current_group)
        winner_username = self.get_username(str(winner))
        losers.remove(winner_username)
        for loser in losers:
            loser_id = self.get_id_from_username(loser)
            if loser_id < 0:
                continue
            self._execute_non_query(
                "UPDATE scoreboard SET defeats=defeats+1 WHERE player_id=?;",
                (loser_id,),
            )

    def create_default_online_player(
        self, username: str, password: str, server: str
    ) -> str:
        """Create a default online player entry and persist it in the repository.

        Args:
            username: Player username used as lookup key in the repository.
            password: Password associated with the player account.
            server: Server value handled.

        Returns:
            None.
        """
        if 3 <= len(username) <= 30:
            self._execute_non_query(
                "INSERT INTO players(username, status, password,"
                " connected, proper_client)"
                " VALUES(?, ?, ?, ?, ?);",
                (username, "idle", password, False, True)
            )
            player_id: int = self.get_id_from_username(username)
            self._execute_non_query(
                "INSERT INTO scoreboard(player_id, victories, defeats)"
                " VALUES(?, 0, 0);",
                (player_id,),
            )
            self._execute_non_query(
                "INSERT INTO usernames(server, username) VALUES(?, ?);",
                (server, username),
            )
            return "Account successfully created."
        else:
            return (
                "Error creating the account, username too long"
                " (min 3 characters, max 30 characters)."
            )

    def check_all_remaining_timeouts(self, timeout: float) -> list[int]:
        """Check all remaining timeouts and return the evaluation result.

        Args:
            timeout: Timeout value in seconds or timestamp
                depending on the context.

        Returns:
            list[int]: Player ids whose timeout expired during this scan.
        """
        rows = self._execute_query(
            "SELECT player_id, timeout_end FROM timeouts;"
        )
        timed_out = []
        for row in rows:
            player_id, timeout_end = row
            if time.time() >= timeout_end:
                timed_out.append(player_id)
                self._execute_non_query(
                    "DELETE FROM timeouts WHERE player_id=?;",
                    (player_id,)
                )
                self.set_proper_client(self.get_username(player_id))
        return timed_out

    def get_remaining_timeout(self, username: str) -> int:
        """Return the remaining timeout from repository data or in-memory state.

        Args:
            username: Player username used as lookup key in the repository.

        Returns:
            int: Remaining timeout in whole seconds, or 0 when none is active.
        """
        player_id = self.get_id_from_username(username)
        rows = self._execute_query(
            "SELECT timeout_end FROM timeouts WHERE player_id=?;",
            (player_id,)
        )
        if not bool(rows):
            return 0
        timeout_end = rows[0]['timeout_end']
        remaining_timeout = int(timeout_end - time.time())
        return max(remaining_timeout, 0)

    def set_timeout_for_player(self, username: str, timeout_duration: float):
        """Update the timeout for player value in the underlying data structure.

        Args:
            username: Player username used as lookup key in the repository.
            timeout_duration: Timeout duration value handled.

        Returns:
            None.
        """
        player_id = self.get_id_from_username(username)
        timeout_end = time.time() + timeout_duration
        rows = self._execute_query(
            "SELECT 1 FROM timeouts WHERE player_id=?;",
            (player_id,)
        )
        if bool(rows):
            self._execute_non_query(
                "UPDATE timeouts SET timeout_end=? WHERE player_id=?;",
                (timeout_end, player_id)
            )
        else:
            self._execute_non_query(
                "INSERT INTO timeouts(player_id, timeout_end) VALUES(?, ?);",
                (player_id, timeout_end)
            )

    def set_new_username_for_server(self, server: str, username: str):
        """Update the new username for server value in the underlying data
        structure.

        Args:
            server: Server value handled.
            username: Player username used as lookup key in the repository.

        Returns:
            None.
        """
        self._execute_non_query(
            "INSERT INTO usernames(server, username) VALUES(?, ?);",
            (server, username),
        )

    def get_online_player(self, server: str) -> str:
        """Return the online player from repository data or in-memory state.

        Args:
            server: Server value handled.

        Returns:
            str: Username reserved as the local identity for this server.
        """
        rows = self._execute_query(
            "SELECT username FROM usernames WHERE server=?;", (server,)
        )
        return rows[0]["username"]

    def has_no_special_username(self, server: str) -> bool:
        """Check whether no special username is available in the current state.

        Args:
            server: Server value handled.

        Returns:
            bool: True when no username is reserved yet for this server.
        """
        rows = self._execute_query(
            "SELECT username FROM usernames WHERE server=?", (server,)
        )
        return not bool(rows)

    def player_exists(self, player_name: str) -> bool:
        """Execute the player exists operation on data state.

        Args:
            player_name: Player name value handled.

        Returns:
            bool: True when a player row exists for `player_name`.
        """
        rows = self._execute_query(
            "SELECT 1 FROM players WHERE username=?;",
            (player_name,),
        )
        return bool(rows)

    def registering(self, username: str, password: str):
        """Execute the registering operation on data state.

        Args:
            username: Player username used as lookup key in the repository.
            password: Password associated with the player account.

        Returns:
            bool: True when login succeeds or account creation completes.
        """
        if self.player_exists(username):
            rows = self._execute_query(
                "SELECT password, connected FROM players WHERE username=?;",
                (username,),
            )
            real_password: str = rows[0]["password"]
            connected: bool = rows[0]["connected"]
            if real_password == password and not connected:
                self._execute_non_query(
                    "UPDATE players SET connected=? WHERE username=?;",
                    (True, username),
                )
                return True
            return False
        else:
            rows_players = self._execute_non_query(
                "INSERT INTO players(username, status, password,"
                " connected, proper_client)"
                " VALUES(?, ?, ?, ?, ?);",
                (username, "idle", password, True, True)
            )
            player_id: int = self.get_id_from_username(username)
            rows_scoreboard = self._execute_non_query(
                "INSERT INTO scoreboard(player_id, victories, defeats)"
                " VALUES(?, 0, 0);",
                (player_id,),
            )
            if bool(rows_players) and bool(rows_scoreboard):
                return True
            return False

    def get_password(self, player_id: int) -> str:
        """Return the password from repository data or in-memory state.

        Args:
            player_id: Identifier of the player targeted.

        Returns:
            str: Password stored for the targeted player id.
        """
        rows = self._execute_query(
            "SELECT password FROM players WHERE player_id=?;", (player_id,)
        )
        return rows[0][0]

    def get_player_profile(self, player_id: int) -> dict[str, Any]:
        """Return the player profile from repository data or in-memory state.

        Args:
            player_id: Identifier of the player targeted.

        Returns:
            dict[str, Any]: Player profile with username, status, win/loss
                counters and derived score, or an empty dict if unknown.
        """
        rows = self._execute_query(
            "SELECT username, status, victories AS stats_win, defeats AS"
            " stats_lose FROM players NATURAL JOIN scoreboard"
            " WHERE player_id=?;",
            (player_id,),
        )
        if not rows:
            return {}
        r = rows[0]
        score = self.get_score(r["stats_win"], r["stats_lose"])
        profile: dict = {k: r[k] for k in r.keys()}
        profile["score"] = score
        return profile

    def get_score(self, wins: int, loses: int):
        """Return the score from repository data or in-memory state.

        Args:
            wins: Wins value handled.
            loses: Loses value handled.

        Returns:
            int: Score derived from wins and losses using repository rules.
        """
        return (wins - loses) % 10

    def get_username(self, player_id: str) -> str:
        """Return the username from repository data or in-memory state.

        Args:
            player_id: Identifier of the player targeted.

        Returns:
            str: Username associated with the given player id.
        """
        rows = self._execute_query(
            "SELECT username FROM players WHERE player_id=?;",
            (int(player_id),),
        )
        return rows[0][0]

    def get_group(self, host_id: int) -> int:
        """Return the group from repository data or in-memory state.

        Args:
            host_id: Identifier of the host targeted.

        Returns:
            int: Group id hosted by `host_id`, or -1 when none exists.
        """
        rows = self._execute_query(
            "SELECT group_id FROM groups WHERE host_player=?;",
            (host_id,)
        )
        if not rows:
            return -1
        return rows[0]["group_id"]

    def party_is_launched(self, host_id: int) -> bool:
        """Execute the party is launched operation on data state.

        Args:
            host_id: Identifier of the host targeted.

        Returns:
            bool: True when the host already has a running game for the party.
        """
        group_id = self.get_group(host_id)
        rows = self._execute_query(
            "SELECT game_id FROM current_games WHERE group_id=?;", (group_id,)
        )
        return bool(rows)

    def get_id_from_username(self, player_username: str) -> int:
        """Return the id from username from repository data or in-memory state.

        Args:
            player_username: Player username value handled.

        Returns:
            int: Player id for `player_username`, or -1 when unknown.
        """
        rows = self._execute_query(
            "SELECT player_id FROM players WHERE username=?;",
            (player_username,),
        )
        if not bool(rows):
            return -1
        return rows[0][0]

    def change_status(self, client_id: str, status: str) -> str:
        """Execute the change status operation on data state.

        Args:
            client_id: Identifier of the client targeted.
            status: New online status value to persist for the player.

        Returns:
            str: Localized status-change result message.
        """
        rows = self._execute_non_query(
            "UPDATE players SET status=? WHERE player_id=?;",
            (
                status,
                int(client_id),
            ),
        )
        if rows is None:
            return _("Status not changed.")
        return _("Status changed to {status}.").format(status=status)

    def get_status(self, client_id: str) -> str:
        """Return the status from repository data or in-memory state.

        Args:
            client_id: Identifier of the client targeted.

        Returns:
            str: Current player status, or `unknown` when no row matches.
        """
        rows = self._execute_query(
            "SELECT status FROM players WHERE player_id=?;",
            (int(client_id),),
        )
        if not rows:
            return "unknown"
        return rows[0][0]

    def current_players(self) -> str:
        """Execute the current players operation on data state.

        Returns:
            str: Human-readable summary of connected non-away players.
        """
        rows = self._execute_query(
            "SELECT player_id, username, status FROM players"
            " WHERE status!='away' AND connected=True;"
        )
        answer = [(r["player_id"], r["username"], r["status"]) for r in rows]
        return _("List of current players: {players}").format(players=answer)

    def invitation_received(self, client_id: str) -> tuple[int, int]:
        """Execute the invitation received operation on data state.

        Args:
            client_id: Identifier of the client targeted.

        Returns:
            tuple[int, int]: `(host_player, group_id)` of the pending
                invitation, or `(-1, -1)` when none exists.
        """
        rows = self._execute_query(
            "SELECT host_player, group_id FROM pending_invitations"
            " NATURAL JOIN groups WHERE invited_player=?;",
            (int(client_id),),
        )
        if rows == []:
            return (-1, -1)
        return rows[0]['host_player'], rows[0]['group_id']

    def accept_invitation(self, group_id: int, invited: str):
        """Execute the accept invitation operation on data state.

        Args:
            group_id: Identifier of the group targeted.
            invited: Invited value handled.
        """
        if self.invitation_received(invited) == (-1, -1):
            return
        self.change_status(invited, "waitgame")
        self._execute_non_query(
            "UPDATE players SET group_id=? WHERE player_id=?;",
            (
                group_id,
                int(invited),
            ),
        )
        rows = self._execute_non_query(
            "DELETE FROM pending_invitations WHERE invited_player=?;",
            (int(invited),),
        )
        rows = self._execute_query(
            "SELECT number_of_players FROM groups WHERE group_id=?;",
            (group_id,),
        )
        rows = self._execute_non_query(
            "UPDATE groups SET number_of_players=?+1 WHERE group_id=?;",
            (rows[0][0], group_id),
        )

    def reject_invitation(self, invited: str):
        """Execute the reject invitation operation on data state.

        Args:
            invited: Invited value handled.

        Returns:
            None.
        """
        self._execute_non_query(
            "DELETE FROM pending_invitations WHERE invited_player=?;",
            (int(invited),),
        )

    def get_game(self, client_id: str) -> int:
        """Return the game from repository data or in-memory state.

        Args:
            client_id: Identifier of the client targeted.

        Returns:
            int: Game id associated with the player's current group.
        """
        rows = self._execute_query(
            "SELECT game_id FROM current_games NATURAL JOIN groups"
            " NATURAL JOIN players WHERE player_id=?;",
            (int(client_id),),
        )
        return rows[0][0]

    def get_game_id(self, group_id: int) -> int:
        """Return the game id from repository data or in-memory state.

        Args:
            group_id: Identifier of the group targeted.

        Returns:
            int: Game id currently attached to `group_id`.
        """
        rows = self._execute_query("SELECT * FROM current_games;")
        rows = self._execute_query(
            "SELECT game_id FROM current_games WHERE group_id=?;", (group_id,)
        )
        return rows[0]["game_id"]

    def check_all_invitations_resolved(self, client_id: str):
        """Check all invitations resolved and return the evaluation result.

        Args:
            client_id: Identifier of the client targeted.

        Returns:
            bool: True when no invitation is still in `waiting` state.
        """
        rows = self._execute_query(
            "SELECT invited_player, username, invitation_status FROM"
            " pending_invitations"
            " NATURAL JOIN players NATURAL JOIN groups WHERE host_player=?;",
            (int(client_id),),
        )
        if not bool(rows):
            return True
        for row in rows:
            if row["invitation_status"] == "waiting":
                return False
        return True

    def get_host_from_party(self, party_id: int) -> int:
        """Return the host from party from repository data or in-memory state.

        Args:
            party_id: Identifier of the party targeted.

        Returns:
            int: Player id of the host owning the targeted party.
        """
        rows = self._execute_query(
            "SELECT host_player FROM groups WHERE group_id=?;", (party_id,)
        )
        return rows[0]["host_player"]

    def get_scoreboard(self) -> list[sqlite3.Row]:
        """Return the scoreboard from repository data or in-memory state.

        Returns:
            list[sqlite3.Row]: Scoreboard rows with player id, username,
                victories, defeats and total games.
        """
        rows = self._execute_query(
            "SELECT player_id AS id, username, victories, defeats,"
            " (victories + defeats) AS total_games FROM scoreboard"
            " NATURAL JOIN players;"
        )
        return rows

    def invitation_sent_from(self, client_id: str) -> list[str]:
        """Execute the invitation sent from operation on data state.

        Args:
            client_id: Identifier of the client targeted.

        Returns:
            list[str]: Invited player ids still waiting for a response.
        """
        group_id = self.get_group(int(client_id))
        rows = self._execute_query(
            "SELECT invited_player FROM pending_invitations "
            " WHERE group_id=? AND invitation_status='waiting';",
            (group_id,),
        )
        return [str(row[0]) for row in rows]

    def cancel_invitation_from(self, client_id: str, players: list[str]):
        """Execute the cancel invitation from operation on data state.

        Args:
            client_id: Identifier of the client targeted.
            players: Players value handled.

        Returns:
            str: Localized message describing the cancellation outcome.
        """
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
                return _("All invitations cancelled.")
            return _("No invitations cancelled.")
        for player_id in players:
            rows = self._execute_non_query(
                "DELETE FROM pending_invitations WHERE invited_player=?;",
                (int(player_id),),
            )
        return _("Your invitation(s) have been cancelled.")

    def check_all_invitations_timeout(self, timeout) -> list[int]:
        """Check all invitations timeout and return the evaluation result.

        Args:
            timeout: Timeout value in seconds or timestamp
                depending on the context.

        Returns:
            list[int]: Invited player ids whose invitation expired.
        """
        rows = self._execute_query(
            "SELECT invitation_id, sending_time, invited_player"
            " FROM pending_invitations;"
        )
        timed_out = []
        for row in rows:
            id, t, invited = row
            if time.time() - t > timeout:
                timed_out.append(invited)
                self.cancel_invitation(id)
        return timed_out

    def cancel_invitation(self, invitation_id: int) -> bool:
        """Execute the cancel invitation operation on data state.

        Args:
            invitation_id: Identifier of the invitation targeted.

        Returns:
            bool: True when a database row was deleted for this invitation.
        """
        rows = self._execute_non_query(
            "DELETE FROM pending_invitations WHERE invitation_id=?;",
            (invitation_id,),
        )
        return bool(rows)

    def get_parties(self) -> list[int]:
        """Return the parties from repository data or in-memory state.

        Returns:
            list[int]: All current group ids stored in the repository.
        """
        rows = self._execute_query("SELECT group_id FROM groups;")
        parties: list[int] = []
        for row in rows:
            parties.append(row["group_id"])
        return parties

    def create_party(self, client_username: str) -> int | None:
        """Create a party entry and persist it in the repository.

        Args:
            client_username: Client username value handled.

        Returns:
            int | None: Newly created party id for the host, if creation
                succeeds.
        """
        host_id: int = self.get_id_from_username(client_username)
        self.change_status(str(host_id), "waitgame")
        self._execute_non_query(
            "INSERT INTO groups(number_of_players, host_player)"
            " VALUES (?, ?);",
            (
                1,
                host_id,
            ),
        )
        rows = self._execute_query(
            "SELECT group_id FROM groups WHERE host_player=?;", (host_id,)
        )
        self._execute_non_query(
            "UPDATE players SET group_id=? WHERE player_id=?;",
            (rows[0]["group_id"], host_id),
        )
        party_id: int = rows[0]["group_id"]
        return party_id

    def get_party(self, client_id: str) -> list[int]:
        """Return the party from repository data or in-memory state.

        Args:
            client_id: Identifier of the client targeted.

        Returns:
            list[int]: Player ids currently belonging to the host's party.
        """
        rows = self._execute_query(
            "SELECT player_id FROM groups NATURAL JOIN players"
            " WHERE host_player=?;",
            (int(client_id),)
        )
        return [r[0] for r in rows]

    def clean_party(self, party: int):
        """Execute the clean party operation on data state.

        Args:
            party: Party value handled.
        """
        check = self.clean_party_players(party)
        if not check:
            print(_("Error cleaning the party's players!"), file=sys.stderr)
            return
        self._execute_non_query(
            "DELETE FROM current_games WHERE group_id=?;", (party,)
        )
        self._execute_non_query(
            "DELETE FROM groups WHERE group_id=?;", (party,)
        )

    def client_quit(self, client_username: str):
        """Execute the client quit operation on data state.

        Args:
            client_username: Client username value handled.
        """
        client_id = self.get_id_from_username(client_username)
        group_id = self.get_party_id(str(client_id))
        if group_id not in (-1, None):
            self.remove_client_from_party(client_username)

        self._execute_non_query(
            "UPDATE players SET connected=?, group_id=?,"
            " status=? WHERE username=?;",
            (False, None, "idle", client_username),
        )

    def remove_client_from_party(self, client_username: str):
        """Execute the remove client from party operation on data state.

        Args:
            client_username: Client username value handled.
        """
        client_id = self.get_id_from_username(client_username)
        group_id = self.get_party_id(str(client_id))
        if group_id in (-1, None):
            return
        host_id = self.get_host_from_party(group_id)
        if host_id == client_id:
            self.clean_party(group_id)
        else:
            self._execute_non_query(
                "UPDATE players SET group_id=?, status=? WHERE player_id=?;",
                (None, "idle", client_id),
            )
            rows = self._execute_query(
                "SELECT number_of_players FROM groups WHERE group_id=?;",
                (group_id,),
            )
            self._execute_non_query(
                "UPDATE groups SET number_of_players=?-1 WHERE group_id=?;",
                (rows[0][0], group_id),
            )

    def set_unproper_client(self, client_username: str):
        """Update the unproper client value in the underlying data structure.

        Args:
            client_username: Client username value handled.
        """
        self._execute_non_query(
            "UPDATE players SET proper_client=? WHERE username=?;",
            (False, client_username)
        )

    def set_proper_client(self, client_username: str):
        """Update the proper client value in the underlying data structure.

        Args:
            client_username: Client username value handled.
        """
        self._execute_non_query(
            "UPDATE players SET proper_client=? WHERE username=?;",
            (True, client_username)
        )

    def is_proper_client(self, client_username: str) -> bool:
        """Check whether proper client is true in the current state.

        Args:
            client_username: Client username value handled.

        Returns:
            bool: Stored `proper_client` flag, defaulting to True if absent.
        """
        rows = self._execute_query(
            "SELECT proper_client FROM players WHERE username=?;",
            (client_username,)
        )
        if not bool(rows):
            return True
        return rows[0]['proper_client']

    def check_party_is_alive(self, group_id: int) -> bool:
        """Check party is alive and return the evaluation result.

        Args:
            group_id: Identifier of the group targeted.

        Returns:
            bool: True when at least one player still belongs to the group.
        """
        rows = self._execute_query(
            "SELECT player_id FROM players WHERE group_id=?;", (group_id,)
        )
        if len(rows) > 0:
            return True
        return False

    def clean_game(self, game_id: int):
        """Execute the clean game operation on data state.

        Args:
            game_id: Identifier of the persisted game targeted.
        """
        self._execute_non_query(
            "DELETE FROM current_games WHERE game_id=?;", (game_id,)
        )

    def get_group_from_game(self, game_id: int) -> int:
        """Return the group from game from repository data or in-memory state.

        Args:
            game_id: Identifier of the persisted game targeted.

        Returns:
            int: Group id attached to the persisted game.
        """
        rows = self._execute_query(
            "SELECT group_id FROM current_games WHERE game_id=?;", (game_id,)
        )
        return rows[0]["group_id"]

    def clean_party_players(self, party: int) -> bool:
        """Execute the clean party players operation on data state.

        Args:
            party: Party value handled.

        Returns:
            bool: True when the SQL update reports a truthy last row id.
        """
        rows = self._execute_non_query(
            "UPDATE players SET group_id=?, status=? WHERE group_id=?;",
            (None, "idle", party),
        )
        return bool(rows)

    def get_party_id(self, client_id: str) -> int:
        """Return the party id from repository data or in-memory state.

        Args:
            client_id: Identifier of the client targeted.

        Returns:
            int: Group id of the player, or -1 when none is assigned.
        """
        rows = self._execute_query(
            "SELECT group_id FROM players WHERE player_id=?;",
            (int(client_id),),
        )
        if bool(rows):
            return rows[0]["group_id"]
        return -1

    def create_game(self, game_name: str, group_id: int):
        """Create a game entry and persist it in the repository.

        Args:
            game_name: Game name value handled.
            group_id: Identifier of the group targeted.
        """
        self._execute_non_query(
            "INSERT INTO current_games(game_name, group_id)" " VALUES(?, ?);",
            (game_name, group_id)
        )

    def send_invitation(
        self, invited_player: str, invitee_player: str
    ) -> bool:
        """Execute the send invitation operation on data state.

        Args:
            invited_player: Invited player value handled.
            invitee_player: Invitee player value handled.

        Returns:
            bool: True when the invitation row is inserted successfully.
        """
        group_id: int = self._execute_query(
            "SELECT group_id FROM groups WHERE host_player=?;",
            (int(invitee_player),)
        )[0][0]
        rows = self._execute_query(
            "SELECT status FROM players WHERE player_id=?;",
            (int(invited_player),),
        )
        status = rows[0]['status']
        if status == "idle":
            rows = self._execute_non_query(
                "INSERT INTO pending_invitations(group_id, invited_player,"
                " invitation_status, sending_time) VALUES(?, ?, ?, ?);",
                (group_id, int(invited_player), "waiting", time.time()),
            )
            return bool(rows)
        return False

    def delete_party(self, party_id: int):
        """Execute the delete party operation on data state.

        Args:
            party_id: Identifier of the party targeted.
        """
        self._execute_non_query(
            "DELETE FROM groups WHERE group_id=?;",
            (party_id,)
        )

    def get_players_from_group(self, group_id: int) -> list[str]:
        """Return the players from group from repository data or in-memory state.

        Args:
            group_id: Identifier of the group targeted.

        Returns:
            list[str]: Usernames of players currently assigned to the group.
        """
        rows = self._execute_query(
            "SELECT username FROM players WHERE group_id=?;", (group_id,)
        )
        players: list[str] = []
        if len(rows) <= 1:
            return players
        for row in rows:
            players.append(row["username"])
        return players

    def close(self):
        """Execute the close operation on data state."""
        try:
            self.db.close()
            self.closed = True
        except Exception:
            pass

    def reopen(self):
        """Execute the reopen operation on data state."""
        self.__post_init__()
        self.closed = False

    def is_database_closed(self):
        """Check whether database closed is true in the current state.

        Returns:
            bool: True when the SQLite connection has been marked as closed.
        """
        return self.closed
