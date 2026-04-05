from carcassonne.datas.seed import Seed


def test_seed_uses_explicit_value_when_provided() -> None:
    seed = Seed(123456)

    assert seed.seed == 123456


def test_generate_seed_uses_pid_and_time(monkeypatch) -> None:
    monkeypatch.setattr("carcassonne.datas.seed.os.getpid", lambda: 321)
    monkeypatch.setattr("carcassonne.datas.seed.time.time", lambda: 9876.5)

    seed = Seed()

    expected = ((int(9876.5 * 10) % 10000) * 321) * 123 % 100000000
    assert seed.seed == expected
    assert Seed.generate_seed() == expected
