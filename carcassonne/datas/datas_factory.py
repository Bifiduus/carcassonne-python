from __future__ import annotations

from functools import lru_cache
from typing import Any

from carcassonne.interfaces.i_datas_factory import (
    IDatasFactory,
)


@lru_cache(maxsize=1)
def _build_registry() -> dict[str, type[Any]]:
    """Create a class-name to class-object registry for datas."""
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
        registry = _build_registry()
        if class_name not in registry:
            available = ", ".join(sorted(registry))
            raise ValueError(
                f"Unknown datas class '{class_name}'. "
                f"Available classes: {available}"
            )
        return registry[class_name](*args, **kwargs)

    def available_classes(self) -> list[str]:
        return sorted(_build_registry().keys())
