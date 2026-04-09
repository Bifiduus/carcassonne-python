from __future__ import annotations

from functools import lru_cache
from typing import Any

from carcassonne.interfaces.i_datas_factory import (
    IDatasFactory,
)


@lru_cache(maxsize=1)
def _build_registry() -> dict[str, type[Any]]:
    """Build the mapping from exported datas class names to classes.

    Returns:
        dict[str, type[Any]]: Registry used by the factory to instantiate
            datas-layer objects by name.
    """
    from carcassonne.datas.deck import Deck
    from carcassonne.datas.game_configuration import GameConfiguration
    from carcassonne.datas.games_repository import GameRepository
    from carcassonne.datas.graph_data import GraphData, Vertex
    from carcassonne.datas.history import History, MoveRecord
    from carcassonne.datas.meeple_data import Meeple
    from carcassonne.datas.seed import Seed
    from carcassonne.datas.tiles_info import Tile, TilesInfo

    return {
        "Deck": Deck,
        "GameConfiguration": GameConfiguration,
        "GameRepository": GameRepository,
        "GraphData": GraphData,
        "History": History,
        "Meeple": Meeple,
        "MoveRecord": MoveRecord,
        "Seed": Seed,
        "Tile": Tile,
        "TilesInfo": TilesInfo,
        "Vertex": Vertex,
    }


class DatasFactory(IDatasFactory):
    """Factory for creating objects from the datas package."""

    def create(self, class_name: str, *args: Any, **kwargs: Any) -> Any:
        """Instantiate one datas class from its registered name.

        Args:
            class_name: Name of the datas class to instantiate.
            *args: Positional arguments forwarded to the target constructor.
            **kwargs: Keyword arguments forwarded to the target constructor.

        Returns:
            Any: Instance of the requested datas class.
        """
        registry = _build_registry()
        if class_name not in registry:
            available = ", ".join(sorted(registry))
            raise ValueError(
                f"Unknown datas class '{class_name}'. "
                f"Available classes: {available}"
            )
        return registry[class_name](*args, **kwargs)

    def available_classes(self) -> list[str]:
        """Return the list of datas classes exposed by the factory.

        Returns:
            list[str]: Sorted class names accepted by `create`.
        """
        return sorted(_build_registry().keys())
