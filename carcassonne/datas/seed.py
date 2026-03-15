"""
This module defines the Seed class used to generate deterministic seeds.
Generated values are based on runtime info when no explicit seed is provided.
"""

import time
import os


class Seed:
    """Store and generate a numeric seed value for reproducible operations."""

    def __init__(self, value: int | None = None) -> None:
        """
        Initialize a seed with either a provided or generated value.

        Args:
            value: Explicit seed value. If None, a seed is generated.
        """
        if value is None:
            self.seed: int = Seed.generate_seed()
        else:
            self.seed = value

    @staticmethod
    def generate_seed() -> int:
        """
        Generate a pseudo-random seed based on process id and current time.

        Returns:
            Integer seed constrained to 8 digits
        """
        pid: int = os.getpid()
        # Use deciseconds to reduce collisions between fast consecutive calls.
        t: int = int(time.time() * 10) % 10000
        return (t * pid) * 123 % 100000000
