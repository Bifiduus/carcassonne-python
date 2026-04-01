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
MINIMAX_DEPTH = 5
MINIMAX_SCORING = "baseline"
SEEDS = list(range(101, 116))
AI_BY_PLAYER = {
    0: "mcts_uct",
    1: "mcts_ml",
    2: "minimax",
    3: "iterative",
    4: "random",
}
OUTPUT_PATH = Path(
    "carcassonne/statistics/results/all_ais_15games_2026-04-01_ai5s.json"
)


def players_order_for_game(game_index):
    rotation = game_index % len(AI_BY_PLAYER)
    order = list(AI_BY_PLAYER.keys())
    return order[rotation:] + order[:rotation]


def configure_current_player(game, current_id):
    ai_name = AI_BY_PLAYER[current_id]
    if ai_name == "mcts_uct":
        game.set_game_configuration("ai_mode", "mcts")
        game.set_game_configuration("ai_mcts_selection", "UCT")
        game.set_game_configuration("ai_time", AI_TIME_SECONDS)
    elif ai_name == "mcts_ml":
        game.set_game_configuration("ai_mode", "mcts")
        game.set_game_configuration("ai_mcts_selection", "ML")
        game.set_game_configuration("ai_time", AI_TIME_SECONDS)
    elif ai_name == "minimax":
        game.set_game_configuration("ai_mode", "minimax")
        game.set_game_configuration("ai_time", AI_TIME_SECONDS)
        game.set_game_configuration("ai_minimax_depth", MINIMAX_DEPTH)
        game.set_game_configuration("ai_minimax_scoring", MINIMAX_SCORING)
    elif ai_name == "iterative":
        game.set_game_configuration("ai_mode", "iterative")
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



def empty_ai_metrics():
    return {
        "turns": 0,
        "score": 0,
        "wins": 0,
        "ties_for_first": 0,
        "mcts_turns": 0,
        "mcts_steps_total": 0,
        "mcts_steps_max_single_turn": 0,
    }



def run_single_game(seed, game_index):
    cfg = {
        "num_ai_players": 4,
        "ai_mode": "random",
        "ai_time": AI_TIME_SECONDS,
        "ai_minimax_depth": MINIMAX_DEPTH,
        "ai_minimax_scoring": MINIMAX_SCORING,
        "ai_mcts_selection": "UCT",
        "river": False,
        "blitz": False,
        "contest": False,
    }
    order = players_order_for_game(game_index)

    with contextlib.redirect_stdout(io.StringIO()):
        game = Game(GraphData(), 5, cfg)
        game.start_new_game(players_order=order, seed=seed)

    for player in game.game_data.players.values():
        player.is_ai = True

    errors = 0
    turns = 0
    stuck = 0
    prev_hist = len(game.game_data.history.past_moves)
    per_ai = {name: empty_ai_metrics() for name in AI_BY_PLAYER.values()}

    while not game.end_game():
        pid = game.get_current_player().get_id()
        ai_name = AI_BY_PLAYER[pid]
        configure_current_player(game, pid)

        try:
            with contextlib.redirect_stdout(io.StringIO()):
                game.play_ai_turn(game)
            per_ai[ai_name]["turns"] += 1
            if ai_name.startswith("mcts"):
                steps = int(getattr(game, "last_mcts_steps", 0) or 0)
                per_ai[ai_name]["mcts_turns"] += 1
                per_ai[ai_name]["mcts_steps_total"] += steps
                per_ai[ai_name]["mcts_steps_max_single_turn"] = max(
                    per_ai[ai_name]["mcts_steps_max_single_turn"],
                    steps,
                )
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

    scores = {}
    for pid, player in game.game_data.players.items():
        ai_name = AI_BY_PLAYER[pid]
        score = player.get_score_int()
        scores[ai_name] = score
        per_ai[ai_name]["score"] = score

    best_score = max(scores.values())
    winners = sorted(name for name, score in scores.items() if score == best_score)
    for ai_name in winners:
        per_ai[ai_name]["ties_for_first"] += 1
        if len(winners) == 1:
            per_ai[ai_name]["wins"] += 1

    return {
        "seed": seed,
        "game_index": game_index,
        "players_order": order,
        "turns": turns,
        "errors": errors,
        "scores": scores,
        "winners": winners,
        "per_ai": per_ai,
    }



def summarize_ai(ai_name, runs):
    ai_runs = [run["per_ai"][ai_name] for run in runs]
    total_mcts_turns = sum(run["mcts_turns"] for run in ai_runs)
    total_mcts_steps = sum(run["mcts_steps_total"] for run in ai_runs)
    return {
        "games": len(ai_runs),
        "wins": sum(run["wins"] for run in ai_runs),
        "win_rate": sum(run["wins"] for run in ai_runs) / len(ai_runs),
        "ties_for_first": sum(run["ties_for_first"] for run in ai_runs),
        "avg_score": statistics.mean(run["score"] for run in ai_runs),
        "avg_turns": statistics.mean(run["turns"] for run in ai_runs),
        "avg_rank_proxy_margin": statistics.mean(
            run["score"] - max(other for other_name, other in runs[idx]["scores"].items() if other_name != ai_name)
            for idx, run in enumerate(ai_runs)
        ),
        "avg_mcts_steps_per_turn": (
            total_mcts_steps / total_mcts_turns if total_mcts_turns else None
        ),
        "avg_mcts_steps_total": (
            total_mcts_steps / len(ai_runs) if total_mcts_turns else None
        ),
        "max_mcts_steps_single_turn": max(
            run["mcts_steps_max_single_turn"] for run in ai_runs
        ),
    }



def build_summary(runs):
    return {
        ai_name: summarize_ai(ai_name, runs)
        for ai_name in AI_BY_PLAYER.values()
    }



def main():
    start = time.time()
    runs = [run_single_game(seed, game_index) for game_index, seed in enumerate(SEEDS)]
    payload = {
        "elapsed_seconds": round(time.time() - start, 2),
        "ai_time_seconds": AI_TIME_SECONDS,
        "ai_minimax_depth": MINIMAX_DEPTH,
        "ai_minimax_scoring": MINIMAX_SCORING,
        "ai_by_player": AI_BY_PLAYER,
        "seeds": SEEDS,
        "summary": build_summary(runs),
        "runs": runs,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
