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
MATCHUPS = ["UCT", "ML"]
OUTPUT_PATH = Path(
    "carcassonne/statistics/results/mcts_vs_random_2026-04-01_ai5s.json"
)


def configure_current_player(game, current_id, mcts_selection):
    if current_id == 0:
        game.set_game_configuration("ai_mode", "mcts")
        game.set_game_configuration("ai_mcts_selection", mcts_selection)
        game.set_game_configuration("ai_time", AI_TIME_SECONDS)
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
        "ai_time": AI_TIME_SECONDS,
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
    mcts_turns = 0
    mcts_steps_total = 0
    mcts_steps_max = 0
    prev_hist = len(game.game_data.history.past_moves)

    while not game.end_game():
        pid = game.get_current_player().get_id()
        configure_current_player(game, pid, mcts_selection)

        try:
            with contextlib.redirect_stdout(io.StringIO()):
                game.play_ai_turn(game)
            if pid == 0:
                steps = int(getattr(game, "last_mcts_steps", 0) or 0)
                mcts_turns += 1
                mcts_steps_total += steps
                mcts_steps_max = max(mcts_steps_max, steps)
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
        "mcts_turns": mcts_turns,
        "mcts_steps_total": mcts_steps_total,
        "mcts_steps_avg_per_mcts_turn": (
            mcts_steps_total / mcts_turns if mcts_turns else 0.0
        ),
        "mcts_steps_max_single_turn": mcts_steps_max,
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
        "avg_mcts_turns": statistics.mean(r["mcts_turns"] for r in runs),
        "avg_mcts_steps_total": statistics.mean(
            r["mcts_steps_total"] for r in runs
        ),
        "avg_mcts_steps_per_turn": statistics.mean(
            r["mcts_steps_avg_per_mcts_turn"] for r in runs
        ),
        "max_mcts_steps_single_turn": max(
            r["mcts_steps_max_single_turn"] for r in runs
        ),
        "total_errors": sum(r["errors"] for r in runs),
    }


def main():
    all_results = {}
    start = time.time()

    for selection in MATCHUPS:
        runs = [run_single_game(seed, selection) for seed in SEEDS]
        all_results[selection] = {
            "summary": summarize(runs),
            "runs": runs,
        }

    payload = {
        "elapsed_seconds": round(time.time() - start, 2),
        "ai_time_seconds": AI_TIME_SECONDS,
        "seeds": SEEDS,
        "results": all_results,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
