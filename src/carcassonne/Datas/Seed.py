import time
import os

class Seed:
    def __init__(self, value=None):
        if value is None:
            self.seed = Seed.generate_seed()
        else:
            self.seed = value

    @staticmethod
    def generate_seed():
        pid = os.getpid()
        t = int(time.time() * 1000) % 10000
        return (t * pid) * 123 % 100000000