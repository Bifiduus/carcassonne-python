from carcassonne.interfaces.i_player_info_service import IPlayerInfoService


class ConcretePlayerInfoService(IPlayerInfoService):
    def get_id(self) -> int:
        return 7

    def get_username(self) -> str:
        return "alice"

    def get_score(self):
        return 42

    def get_color(self) -> str:
        return "blue"

    def is_ai_player(self) -> bool:
        return False

    def get_number_of_players(self) -> int:
        return 2

    def get_current_player(self):
        return "current"

    def get_score_int(self) -> int:
        return 42

    def get_meeples(self) -> int:
        return 6


def test_i_player_info_service_declares_expected_abstract_methods() -> None:
    assert IPlayerInfoService.__abstractmethods__ == {
        "get_id",
        "get_username",
        "get_score",
        "get_color",
        "is_ai_player",
        "get_number_of_players",
        "get_current_player",
        "get_score_int",
        "get_meeples",
    }


def test_concrete_implementation_satisfies_contract() -> None:
    service = ConcretePlayerInfoService()

    assert service.get_id() == 7
    assert service.get_username() == "alice"
    assert service.get_score() == 42
    assert service.get_color() == "blue"
    assert service.is_ai_player() is False
    assert service.get_number_of_players() == 2
    assert service.get_current_player() == "current"
    assert service.get_score_int() == 42
    assert service.get_meeples() == 6


def test_cannot_instantiate_abstract_service_directly() -> None:
    try:
        IPlayerInfoService()
    except TypeError as exc:
        assert "abstract" in str(exc).lower()
    else:
        assert False, "IPlayerInfoService should remain abstract"
