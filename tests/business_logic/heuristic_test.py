from carcassonne.business_logic.heuristic import (
    HeuristicWeights,
    evaluate_state,
    extract_features,
)


class DummyScore:
    def __init__(self, score=0):
        self.score = score


class DummyPlayer:
    def __init__(self, player_id, meeples=7, score=0):
        self.id = player_id
        self.meeples = meeples
        self._score = DummyScore(score)

    def get_id(self):
        return self.id

    def get_score(self):
        return self._score


class DummyGraph:
    def __init__(self):
        self.lands_components = {"C": {}, "R": {}, "M": {}, "F": {}}

    def get_meeples(self):
        return []


class DummyGameData:
    def __init__(self, player_meeples=7, opponent_meeples=7):
        self.players = {
            0: DummyPlayer(0, meeples=player_meeples),
            1: DummyPlayer(1, meeples=opponent_meeples),
        }
        self.graph = DummyGraph()


class DummyGameState:
    def __init__(self, player_meeples=7, opponent_meeples=7):
        self.game_data = DummyGameData(player_meeples, opponent_meeples)


def test_extract_features_treats_committed_meeples_as_positive():
    game_state = DummyGameState(player_meeples=6, opponent_meeples=7)

    features = extract_features(game_state, 0, 1)

    assert features["meeple_diff"] == 1.0


def test_evaluate_state_improves_when_only_meeple_commitment_changes():
    neutral_state = DummyGameState(player_meeples=7, opponent_meeples=7)
    committed_state = DummyGameState(player_meeples=6, opponent_meeples=7)
    weights = HeuristicWeights(
        score_diff=0.0,
        meeple_diff=10.0,
        latent_score_diff=0.0,
        incomplete_city_tiles_diff=0.0,
        risky_fields_lt3_diff=0.0,
    )

    neutral_eval = evaluate_state(neutral_state, 0, 1, weights)
    committed_eval = evaluate_state(committed_state, 0, 1, weights)

    assert committed_eval > neutral_eval
