from carcassonne.interfaces.i_player import IPlayer
from carcassonne.interfaces.i_player_score import IPlayerScore


class PlayerScore(IPlayerScore):
    id: int
    score: int

    def __init__(self, id: int):
        """Initialise a player's score to 0.

        Args:
            id: Unique player identifier.
        """
        self.id = id
        self.score = 0

    def add_score(self, score: int) -> None:
        """Add points to the player's current score.

        Args:
            score: Number of points to add.

        Returns:
            None. Mutates `self.score` in place.
        """
        self.score += score

    def set_points(self, points: int) -> None:
        """Set the player's score to an exact value.

        Args:
            points: New score value.

        Returns:
            None. Overwrites `self.score`.
        """
        self.score = points


class Player(IPlayer):

    id: int
    name: str
    score: PlayerScore
    color: str
    meeples: int
    is_ai: bool

    def __init__(self, id: int, name: str, color: str, is_ai: bool = False):
        """Initialise a player.

        Args:
            id: Unique player identifier.
            name: Display name.
            color: Meeple color (e.g. ``"red"``, ``"blue"``).
            is_ai: Whether this player is controlled by the AI.
        """
        self.id = id
        self.name = name
        self.color = color
        self.score = PlayerScore(id)
        self.meeples = 7
        self.is_ai = is_ai

    def __str__(self) -> str:
        """Return a human-readable summary of the player's state."""
        return (
            f"{self.name} ({self.color}) - "
            f"Score: {self.score}, Meeples: {self.meeples}"
        )

    def remove_meeple(self) -> None:
        """Remove one meeple from the player's stock.

        Does nothing when the stock is already empty.

        Returns:
            None. Decrements `self.meeples` in place.
        """
        if self.meeples > 0:
            self.meeples -= 1

    def add_meeple(self) -> None:
        """Return one meeple to the player's stock.

        Returns:
            None. Increments `self.meeples` in place.
        """
        self.meeples += 1

    def get_id(self) -> int:
        """Return the player's unique identifier."""
        return self.id

    def get_username(self) -> str:
        """Return the player's display name."""
        return self.name

    def get_score(self) -> PlayerScore:
        """Return the player's `PlayerScore` object."""
        return self.score

    def get_score_int(self) -> int:
        """Return the player's current score as a plain integer."""
        return self.score.score

    def get_color(self) -> str:
        """Return the player's meeple color."""
        return self.color

    def is_ai_player(self) -> bool:
        """Return True when this player is controlled by the AI."""
        return self.is_ai

    def get_meeples(self) -> int:
        """Return the number of meeples currently in the player's stock."""
        return self.meeples

    def set_color(self, color: str) -> None:
        """Set the player's meeple color if it is a valid choice.

        Valid colors: ``"green"``, ``"red"``, ``"blue"``, ``"yellow"``,
          ``"black"``, ``"white"``.
        Silently ignores invalid values.

        Args:
            color: The new color to assign.

        Returns:
            None.
        """
        if color in ["green", "red", "blue", "yellow", "black", "white"]:
            self.color = color

    def reset(self) -> None:
        """Reset the player's score and meeples to their initial values."""
        self.score = PlayerScore(self.id)
        self.meeples = 7
