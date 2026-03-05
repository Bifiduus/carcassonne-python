import pytest
from carcassonne.Datas.Seed import Seed


class TestSeed:
    def test_seed_consistency(self):
        seed1 = Seed(42)
        seed2 = Seed(42)
        assert seed1.seed == seed2.seed, "Seeds with the same value should be equal"
        assert seed1.seed == 42, "Seed value should be set correctly"

    def test_seed_generation(self):
        seed1 = Seed()
        seed2 = Seed()
        assert isinstance(seed1.seed, int), "Generated seed should be an integer"
        assert isinstance(seed2.seed, int), "Generated seed should be an integer"