from unittest.mock import patch

import pytest

from carcassonne.datas.games_repository import GameRepository


@pytest.fixture
def repo(tmp_path, monkeypatch):
    db_path = tmp_path / "carcassonne-test.db"
    monkeypatch.setattr(GameRepository, "db_path", str(db_path))
    repository = GameRepository()
    yield repository
    repository.close()


def test_account_creation_registration_and_profile_queries(repo) -> None:
    assert repo.is_accounted_for() is False
    assert repo.has_no_special_username("srv1") is True
    assert "username too long" in repo.create_default_online_player(
        "ab", "pw", "srv0"
    )

    assert (
        repo.create_default_online_player("alice", "pw", "srv1")
        == "Account successfully created."
    )

    alice_id = repo.get_id_from_username("alice")
    assert repo.is_accounted_for() is True
    assert repo.player_exists("alice") is True
    assert repo.get_next_available_id() == alice_id + 1
    assert repo.get_online_player("srv1") == "alice"
    assert repo.has_no_special_username("srv1") is False
    assert repo.get_password(alice_id) == "pw"
    assert repo.get_username(alice_id) == "alice"
    assert repo.get_player_profile(999) == {}
    assert repo.get_player_profile(alice_id) == {
        "username": "alice",
        "status": "idle",
        "stats_win": 0,
        "stats_lose": 0,
        "score": 0,
    }
    assert repo.get_score(6, 2) == 4
    assert repo.get_id_from_username("nobody") == -1

    assert repo.registering("alice", "wrong") is False
    assert repo.registering("alice", "pw") is True
    assert repo.registering("bob", "pw2") is True

    assert "away" in repo.change_status(str(alice_id), "away")
    assert repo.get_status(str(alice_id)) == "away"
    assert repo.get_status("999") == "unknown"

    current_players = repo.current_players()
    assert "bob" in current_players
    assert "alice" not in current_players

    repo.client_quit("alice")
    assert repo.get_status(str(alice_id)) == "idle"


def test_timeout_and_client_flags_round_trip(repo) -> None:
    assert repo.registering("alice", "pw") is True
    alice_id = repo.get_id_from_username("alice")

    assert repo.is_proper_client("alice")
    repo.set_unproper_client("alice")
    assert not repo.is_proper_client("alice")
    repo.set_new_username_for_server("srv2", "alice")
    assert repo.get_online_player("srv2") == "alice"

    with patch("carcassonne.datas.games_repository.time.time", return_value=100.0):
        repo.set_timeout_for_player("alice", 10)
        assert repo.get_remaining_timeout("alice") == 10

    with patch("carcassonne.datas.games_repository.time.time", return_value=105.0):
        assert repo.get_remaining_timeout("alice") == 5
        assert repo.check_all_remaining_timeouts(10) == []

    with patch("carcassonne.datas.games_repository.time.time", return_value=111.0):
        assert repo.get_remaining_timeout("alice") == 0
        assert repo.check_all_remaining_timeouts(10) == [alice_id]

    assert repo.is_proper_client("alice")
    assert repo.get_remaining_timeout("alice") == 0


def test_party_invitation_game_and_cleanup_flow(repo) -> None:
    assert repo.registering("host", "pw") is True
    assert repo.registering("guest", "pw") is True
    assert repo.registering("busy", "pw") is True
    host_id = repo.get_id_from_username("host")
    guest_id = repo.get_id_from_username("guest")
    busy_id = repo.get_id_from_username("busy")

    party_id = repo.create_party("host")

    assert repo.get_group(host_id) == party_id
    assert repo.get_host_from_party(party_id) == host_id
    assert repo.get_party(str(host_id)) == [host_id]
    assert repo.get_players_from_group(party_id) == []
    assert party_id in repo.get_parties()

    repo.change_status(str(busy_id), "away")
    assert repo.send_invitation(str(busy_id), str(host_id)) is False
    assert repo.send_invitation(str(guest_id), str(host_id)) is True
    assert repo.invitation_received(str(guest_id)) == (host_id, party_id)
    assert repo.invitation_sent_from(str(host_id)) == [str(guest_id)]
    assert repo.check_all_invitations_resolved(str(host_id)) is False

    repo.accept_invitation(party_id, str(guest_id))

    assert sorted(repo.get_party(str(host_id))) == [host_id, guest_id]
    assert repo.get_party_id(str(guest_id)) == party_id
    assert sorted(repo.get_players_from_group(party_id)) == ["guest", "host"]
    assert repo.check_party_is_alive(party_id) is True

    repo.create_game("match", party_id)
    game_id = repo.get_game_id(party_id)

    assert repo.party_is_launched(host_id) is True
    assert repo.get_game(str(guest_id)) == game_id
    assert repo.get_group_from_game(game_id) == party_id

    repo.clean_party(party_id)

    assert repo.check_party_is_alive(party_id) is False
    assert party_id not in repo.get_parties()
    assert repo.get_party_id(str(guest_id)) is None


def test_invitation_timeout_rejection_and_database_lifecycle(repo) -> None:
    assert repo.registering("host", "pw") is True
    assert repo.registering("guest", "pw") is True
    host_id = repo.get_id_from_username("host")
    guest_id = repo.get_id_from_username("guest")
    party_id = repo.create_party("host")

    with patch("carcassonne.datas.games_repository.time.time", return_value=100.0):
        assert repo.send_invitation(str(guest_id), str(host_id)) is True

    repo.reject_invitation(str(guest_id))
    assert repo.invitation_received(str(guest_id)) == (-1, -1)

    with patch("carcassonne.datas.games_repository.time.time", return_value=100.0):
        assert repo.send_invitation(str(guest_id), str(host_id)) is True
    with patch("carcassonne.datas.games_repository.time.time", return_value=200.0):
        assert repo.check_all_invitations_timeout(50) == [guest_id]
    assert repo.invitation_received(str(guest_id)) == (-1, -1)

    assert repo.send_invitation(str(guest_id), str(host_id)) is True
    assert "cancelled" in repo.cancel_invitation_from(
        str(host_id), [str(guest_id)]
    )
    assert repo.invitation_sent_from(str(host_id)) == []

    assert repo.send_invitation(str(guest_id), str(host_id)) is True
    assert "All invitations cancelled." == repo.cancel_invitation_from(
        str(host_id), []
    )

    repo.delete_party(party_id)
    assert party_id not in repo.get_parties()

    assert repo.is_database_closed() is False
    repo.close()
    assert repo.is_database_closed() is True
    repo.reopen()
    assert repo.is_database_closed() is False
    assert repo.player_exists("host") is True
