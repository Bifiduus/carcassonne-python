import time
import os

class Seed:
    def __init__(self, value: int | None = None) -> None:
        if value is None:
            self.seed: int = Seed.generate_seed()
        else:
            self.seed = value

    @staticmethod
    def generate_seed() -> int:
        pid: int = os.getpid()
        t: int = int(time.time() * 10) % 10000
        return (t * pid) * 123 % 100000000