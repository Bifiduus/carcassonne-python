from __future__ import annotations

from functools import lru_cache
from typing import Any

from carcassonne.interfaces.i_business_logic_factory import (
    IBusinessLogicFactory,
)


@lru_cache(maxsize=1)
def _build_registry() -> dict[str, type[Any]]:
    """Create a class-name to class-object registry for business logic."""
    from carcassonne.business_logic.ai.expectimax_player import (
        ExpectimaxPlayer,
        IterativeDeepeningPlayer,
    )
    from carcassonne.business_logic.ai.mcts_player import MCTSNode, MCTSPlayer
    from carcassonne.business_logic.ai.random_player import RandomPlayer
    from carcassonne.business_logic.client import Client
    from carcassonne.business_logic.contest_manager import ContestManager
    from carcassonne.business_logic.game.blitz_manager import BlitzManager
    from carcassonne.business_logic.game.board import Board
    from carcassonne.business_logic.game.commands_game import CommandsGame
    from carcassonne.business_logic.game.deck_manager import DeckManager
    from carcassonne.business_logic.game.end_game import EndGame
    from carcassonne.business_logic.game.game import Game
    from carcassonne.business_logic.game.game_data import GameData
    from carcassonne.business_logic.game.new_game import NewGame
    from carcassonne.business_logic.game.river_manager import RiverManager
    from carcassonne.business_logic.game.undo_redo_manager import (
        UndoRedoManager,
    )
    from carcassonne.business_logic.game_mode_manager import GameModeManager
    from carcassonne.business_logic.graph_logic import GraphLogic
    from carcassonne.business_logic.heuristic import HeuristicWeights
    from carcassonne.business_logic.heuristic_disruption import (
        DisruptionWeights,
    )
    from carcassonne.business_logic.heuristic_short_term import (
        ShortTermWeights,
    )
    from carcassonne.business_logic.online_communication import (
        OnlineCommunication,
    )
    from carcassonne.business_logic.player import Player, PlayerScore
    from carcassonne.business_logic.rules_manager import RulesManager
    from carcassonne.business_logic.save_handler import SaveHandler
    from carcassonne.business_logic.score_manager import ScoreManager
    from carcassonne.business_logic.server import Server

    return {
        "BlitzManager": BlitzManager,
        "Board": Board,
        "Client": Client,
        "CommandsGame": CommandsGame,
        "ContestManager": ContestManager,
        "DeckManager": DeckManager,
        "DisruptionWeights": DisruptionWeights,
        "EndGame": EndGame,
        "ExpectimaxPlayer": ExpectimaxPlayer,
        "Game": Game,
        "GameData": GameData,
        "GameModeManager": GameModeManager,
        "GraphLogic": GraphLogic,
        "HeuristicWeights": HeuristicWeights,
        "IterativeDeepeningPlayer": IterativeDeepeningPlayer,
        "MCTSNode": MCTSNode,
        "MCTSPlayer": MCTSPlayer,
        "NewGame": NewGame,
        "OnlineCommunication": OnlineCommunication,
        "Player": Player,
        "PlayerScore": PlayerScore,
        "RandomPlayer": RandomPlayer,
        "RiverManager": RiverManager,
        "RulesManager": RulesManager,
        "SaveHandler": SaveHandler,
        "ScoreManager": ScoreManager,
        "Server": Server,
        "ShortTermWeights": ShortTermWeights,
        "UndoRedoManager": UndoRedoManager,
    }


class BusinessLogicFactory(IBusinessLogicFactory):
    """Factory for creating objects from the business_logic package."""

    def create(self, class_name: str, *args: Any, **kwargs: Any) -> Any:
        registry = _build_registry()
        if class_name not in registry:
            available = ", ".join(sorted(registry))
            raise ValueError(
                f"Unknown business_logic class '{class_name}'. "
                f"Available classes: {available}"
            )
        return registry[class_name](*args, **kwargs)

    def available_classes(self) -> list[str]:
        return sorted(_build_registry().keys())
