import contextlib
import io
import json
import statistics
import time
from pathlib import Path

from carcassonne.business_logic.ai_model import RandomPlayer
from carcassonne.business_logic.game.game import Game
from carcassonne.datas.graph_data import GraphData

AI_TIME_SECONDS = 5
SEEDS = [101, 202, 303, 404, 505]
MATCHUPS = ["minimax", "iterative"]
MINIMAX_DEPTH = 5
MINIMAX_SCORING = "baseline"
OUTPUT_PATH = Path(
    "carcassonne/statistics/results/minimax_iterative_vs_random_2026-04-01_ai5s.json"
)


def configure_current_player(game, current_id, ai_mode):
    if current_id == 0:
        game.set_game_configuration("ai_mode", ai_mode)
        game.set_game_configuration("ai_time", AI_TIME_SECONDS)
        game.set_game_configuration("ai_minimax_depth", MINIMAX_DEPTH)
        game.set_game_configuration("ai_minimax_scoring", MINIMAX_SCORING)
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


def run_single_game(seed, ai_mode):
    cfg = {
        "num_ai_players": 4,
        "ai_mode": "random",
        "ai_time": AI_TIME_SECONDS,
        "ai_minimax_depth": MINIMAX_DEPTH,
        "ai_minimax_scoring": MINIMAX_SCORING,
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
        configure_current_player(game, pid, ai_mode)

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


def main():
    all_results = {}
    start = time.time()

    for ai_mode in MATCHUPS:
        runs = [run_single_game(seed, ai_mode) for seed in SEEDS]
        all_results[ai_mode] = {
            "summary": summarize(runs),
            "runs": runs,
        }

    payload = {
        "elapsed_seconds": round(time.time() - start, 2),
        "ai_time_seconds": AI_TIME_SECONDS,
        "ai_minimax_depth": MINIMAX_DEPTH,
        "ai_minimax_scoring": MINIMAX_SCORING,
        "seeds": SEEDS,
        "results": all_results,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
