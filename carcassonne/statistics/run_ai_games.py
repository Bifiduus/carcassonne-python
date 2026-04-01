import contextlib
import io
import json
import statistics
import time

from carcassonne.business_logic.game.game import Game
from carcassonne.business_logic.ai_model import RandomPlayer
from carcassonne.datas.graph_data import GraphData


def configure_current_player(game, current_id, mcts_selection):
    if current_id == 0:
        game.set_game_configuration("ai_mode", "mcts")
        game.set_game_configuration("ai_mcts_selection", mcts_selection)
        game.set_game_configuration("ai_time", 1)
    else:
        game.set_game_configuration("ai_mode", "random")
        game.set_game_configuration("ai_time", 1)


def random_fallback_move(game):
    if game.game_data.current_hand is None:
        with contextlib.redirect_stdout(io.StringIO()):
            game.draw_tile(silent=True)
    tile = game.game_data.current_hand
    if tile is None:
        return False
    model = RandomPlayer()
    move = model.random_move(tile, game)
    if not move:
        return False
    with contextlib.redirect_stdout(io.StringIO()):
        return bool(game.play_move(move))


def run_single_game(seed, mcts_selection):
    cfg = {
        "num_ai_players": 4,
        "ai_mode": "random",
        "ai_time": 1,
        "ai_mcts_selection": mcts_selection,
        "river": False,
        "blitz": False,
        "contest": False,
    }
    with contextlib.redirect_stdout(io.StringIO()):
        game = Game(GraphData(), 5, cfg)
        game.start_new_game(players_order=[0, 1, 2, 3, 4], seed=seed)

    for player in game.game_data.players.values():
        player.is_ai = True

    errors = 0
    turns = 0
    stuck = 0
    prev_hist = len(game.game_data.history.past_moves)

    while not game.end_game():
        pid = game.get_current_player().get_id()
        configure_current_player(game, pid, mcts_selection)

        try:
            with contextlib.redirect_stdout(io.StringIO()):
                game.play_ai_turn(game)
        except Exception:
            errors += 1
            if not random_fallback_move(game):
                break

        turns += 1
        curr_hist = len(game.game_data.history.past_moves)
        if curr_hist == prev_hist:
            stuck += 1
        else:
            stuck = 0
        prev_hist = curr_hist

        if stuck >= 10 or turns > 500:
            break

    with contextlib.redirect_stdout(io.StringIO()):
        game.end_game()

    scores = {pid: p.get_score_int() for pid, p in game.game_data.players.items()}
    best = max(scores.values())
    winners = sorted(pid for pid, s in scores.items() if s == best)
    opp_best = max(v for k, v in scores.items() if k != 0)

    return {
        "seed": seed,
        "turns": turns,
        "errors": errors,
        "scores": scores,
        "winners": winners,
        "target_score": scores[0],
        "target_win": winners == [0],
        "target_tie_first": 0 in winners,
        "target_margin_vs_best_opp": scores[0] - opp_best,
    }


def summarize(runs):
    return {
        "games": len(runs),
        "wins": sum(1 for r in runs if r["target_win"]),
        "win_rate": sum(1 for r in runs if r["target_win"]) / len(runs),
        "ties_for_first": sum(
            1 for r in runs if r["target_tie_first"] and not r["target_win"]
        ),
        "avg_target_score": statistics.mean(r["target_score"] for r in runs),
        "avg_margin_vs_best_opponent": statistics.mean(
            r["target_margin_vs_best_opp"] for r in runs
        ),
        "avg_turns": statistics.mean(r["turns"] for r in runs),
        "total_errors": sum(r["errors"] for r in runs),
    }


seeds = [101, 202, 303, 404, 505]
matchups = ["UCT", "ML"]
all_results = {}
start = time.time()

for selection in matchups:
    runs = [run_single_game(seed, selection) for seed in seeds]
    all_results[selection] = {
        "summary": summarize(runs),
        "runs": runs,
    }

print(json.dumps({
    "elapsed_seconds": round(time.time() - start, 2),
    "seeds": seeds,
    "results": all_results,
}, indent=2))