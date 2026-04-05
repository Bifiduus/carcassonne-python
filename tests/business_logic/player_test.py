from carcassonne.business_logic.player import Player


def test_player_exposes_identity_score_and_ai_state() -> None:
    player = Player(2, "Alice", "green", is_ai=True)
    player.get_score().add_score(7)

    assert player.get_id() == 2
    assert player.get_username() == "Alice"
    assert player.get_score_int() == 7
    assert player.get_color() == "green"
    assert player.is_ai_player() is True
    assert "Alice" in str(player)


def test_player_meeple_stock_cannot_drop_below_zero() -> None:
    player = Player(0, "Bob", "red")

    for _ in range(10):
        player.remove_meeple()

    player.add_meeple()

    assert player.get_meeples() == 1


def test_player_reset_restores_score_meeples_and_preserves_valid_color_rules() -> None:
    player = Player(1, "Cara", "blue")
    player.get_score().add_score(12)
    player.remove_meeple()
    player.set_color("yellow")
    player.set_color("not-a-color")

    assert player.get_color() == "yellow"

    player.reset()

    assert player.get_score_int() == 0
    assert player.get_meeples() == 7
    assert player.get_color() == "yellow"
