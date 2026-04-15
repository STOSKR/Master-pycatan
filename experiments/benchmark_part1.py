from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime as dt
import importlib
import itertools
import json
import os
import platform
from pathlib import Path
import random
import subprocess
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence

# Allow running this script directly from the experiments folder.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PyCatan.Managers.GameDirector import GameDirector


DEFAULT_AGENT_CLASS = (
    "PyCatan.Agents.AlexPelochoJaimeHeuristicAgent.AlexPelochoJaimeHeuristicAgent"
)

RANDOM_AGENT_CLASS = "PyCatan.Agents.RandomAgent.RandomAgent"

STANDARD_AGENT_POOL = [
    RANDOM_AGENT_CLASS,
    "PyCatan.Agents.AdrianHerasAgent.AdrianHerasAgent",
    "PyCatan.Agents.AlexPastorAgent.AlexPastorAgent",
    "PyCatan.Agents.CarlesZaidaAgent.CarlesZaidaAgent",
    "PyCatan.Agents.CrabisaAgent.CrabisaAgent",
    "PyCatan.Agents.EdoAgent.EdoAgent",
    "PyCatan.Agents.PabloAleixAlexAgent.PabloAleixAlexAgent",
    "PyCatan.Agents.SigmaAgent.SigmaAgent",
    "PyCatan.Agents.TristanAgent.TristanAgent",
]


@dataclass(frozen=True)
class MatchTask:
    mode: str
    target_class_path: str
    opponent_class_paths: Sequence[str]
    position: int
    max_rounds: int
    seed: int


def load_class(class_path: str):
    module_name, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def parse_match_result(trace: Dict, position: int) -> Dict[str, float]:
    game_rounds = trace["game"]
    last_round = max(game_rounds.keys(), key=lambda key: int(key.split("_")[-1]))
    turns = game_rounds[last_round]
    last_turn = max(turns.keys(), key=lambda key: int(key.split("_")[-1].lstrip("P")))

    victory_points = turns[last_turn]["end_turn"]["victory_points"]
    agent_id = f"J{position}"
    points = int(victory_points[agent_id])

    winner = max(victory_points.items(), key=lambda pair: int(pair[1]))[0]
    win = 1 if winner == agent_id else 0

    ranking = sorted(victory_points.items(), key=lambda pair: int(pair[1]), reverse=True)
    rank = 4
    for idx, (player_id, _) in enumerate(ranking, start=1):
        if player_id == agent_id:
            rank = idx
            break

    return {
        "win": float(win),
        "points": float(points),
        "rank": float(rank),
    }


def simulate_task(task: MatchTask) -> Dict:
    random.seed(task.seed)

    try:
        target_class = load_class(task.target_class_path)
        opponents = [load_class(path) for path in task.opponent_class_paths]

        agents = list(opponents)
        agents.insert(task.position, target_class)

        game_director = GameDirector(agents=agents, max_rounds=task.max_rounds, store_trace=False)
        trace = game_director.game_start(print_outcome=False)
        parsed = parse_match_result(trace, task.position)

        return {
            "ok": True,
            "mode": task.mode,
            "position": task.position,
            "seed": task.seed,
            "opponents": list(task.opponent_class_paths),
            **parsed,
        }
    except Exception as exc:
        return {
            "ok": False,
            "mode": task.mode,
            "position": task.position,
            "seed": task.seed,
            "opponents": list(task.opponent_class_paths),
            "error": repr(exc),
        }


def build_random_tasks(
    target_class_path: str,
    games_per_position: int,
    max_rounds: int,
    seed: int,
) -> List[MatchTask]:
    tasks: List[MatchTask] = []
    for position in range(4):
        for game_idx in range(games_per_position):
            tasks.append(
                MatchTask(
                    mode="random",
                    target_class_path=target_class_path,
                    opponent_class_paths=[RANDOM_AGENT_CLASS, RANDOM_AGENT_CLASS, RANDOM_AGENT_CLASS],
                    position=position,
                    max_rounds=max_rounds,
                    seed=seed + position * 100_000 + game_idx,
                )
            )
    return tasks


def build_standard_tasks(
    target_class_path: str,
    games_per_position: int,
    max_rounds: int,
    seed: int,
    max_permutations: int,
) -> List[MatchTask]:
    pool = [path for path in STANDARD_AGENT_POOL if path != target_class_path]
    permutations = list(itertools.permutations(pool, 3))

    if max_permutations > 0 and len(permutations) > max_permutations:
        chooser = random.Random(seed)
        permutations = chooser.sample(permutations, max_permutations)

    tasks: List[MatchTask] = []
    for perm_idx, opponents in enumerate(permutations):
        for position in range(4):
            for game_idx in range(games_per_position):
                tasks.append(
                    MatchTask(
                        mode="standard",
                        target_class_path=target_class_path,
                        opponent_class_paths=list(opponents),
                        position=position,
                        max_rounds=max_rounds,
                        seed=seed + perm_idx * 1_000_000 + position * 10_000 + game_idx,
                    )
                )
    return tasks


def summarize_results(results: Iterable[Dict]) -> List[Dict]:
    grouped: Dict[str, List[Dict]] = {}
    for result in results:
        grouped.setdefault(result["mode"], []).append(result)

    rows: List[Dict] = []
    for mode, mode_results in grouped.items():
        successful = [item for item in mode_results if item.get("ok")]
        errors = [item for item in mode_results if not item.get("ok")]

        if successful:
            rows.append(
                {
                    "mode": mode,
                    "segment": "overall",
                    "position": "all",
                    "games": len(successful),
                    "wins": int(sum(item["win"] for item in successful)),
                    "win_rate": sum(item["win"] for item in successful) / len(successful),
                    "avg_points": sum(item["points"] for item in successful) / len(successful),
                    "avg_rank": sum(item["rank"] for item in successful) / len(successful),
                    "errors": len(errors),
                }
            )

            for position in range(4):
                subset = [item for item in successful if item["position"] == position]
                if not subset:
                    continue

                rows.append(
                    {
                        "mode": mode,
                        "segment": "position",
                        "position": position,
                        "games": len(subset),
                        "wins": int(sum(item["win"] for item in subset)),
                        "win_rate": sum(item["win"] for item in subset) / len(subset),
                        "avg_points": sum(item["points"] for item in subset) / len(subset),
                        "avg_rank": sum(item["rank"] for item in subset) / len(subset),
                        "errors": 0,
                    }
                )
        else:
            rows.append(
                {
                    "mode": mode,
                    "segment": "overall",
                    "position": "all",
                    "games": 0,
                    "wins": 0,
                    "win_rate": 0.0,
                    "avg_points": 0.0,
                    "avg_rank": 0.0,
                    "errors": len(errors),
                }
            )

    return rows


def git_info() -> Dict[str, str]:
    def run_git(args: List[str]) -> str:
        return subprocess.check_output(["git", *args], text=True).strip()

    try:
        commit = run_git(["rev-parse", "HEAD"])
    except Exception:
        commit = "unknown"

    try:
        dirty = bool(run_git(["status", "--porcelain"]))
    except Exception:
        dirty = True

    return {"commit": commit, "dirty": str(dirty).lower()}


def main() -> int:
    parser = argparse.ArgumentParser(description="Part 1 benchmark runner for heuristic Catan agents")
    parser.add_argument("--agent-class", default=DEFAULT_AGENT_CLASS)
    parser.add_argument("--mode", choices=["random", "standard", "both"], default="both")
    parser.add_argument("--games-per-position", type=int, default=40)
    parser.add_argument("--max-rounds", type=int, default=200)
    parser.add_argument("--workers", type=int, default=max(1, int((os.cpu_count() or 1) * 0.8)))
    parser.add_argument("--max-standard-permutations", type=int, default=80)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output-dir", default="experiments/results")
    parser.add_argument("--label", default="part1")
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args()

    repo_info = git_info()
    if repo_info["dirty"] == "true" and not args.allow_dirty:
        print("Refusing to run with dirty worktree. Re-run with --allow-dirty if intentional.")
        return 2

    os.makedirs(args.output_dir, exist_ok=True)

    tasks: List[MatchTask] = []
    if args.mode in ("random", "both"):
        tasks.extend(
            build_random_tasks(
                target_class_path=args.agent_class,
                games_per_position=args.games_per_position,
                max_rounds=args.max_rounds,
                seed=args.seed,
            )
        )

    if args.mode in ("standard", "both"):
        tasks.extend(
            build_standard_tasks(
                target_class_path=args.agent_class,
                games_per_position=args.games_per_position,
                max_rounds=args.max_rounds,
                seed=args.seed,
                max_permutations=args.max_standard_permutations,
            )
        )

    started_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    print(f"Running {len(tasks)} matches with {args.workers} workers...")

    results: List[Dict] = []
    with concurrent.futures.ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(simulate_task, task) for task in tasks]
        for idx, future in enumerate(concurrent.futures.as_completed(futures), start=1):
            result = future.result()
            results.append(result)
            if idx % 100 == 0 or idx == len(tasks):
                print(f"Progress: {idx}/{len(tasks)}")

    finished_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    summary_rows = summarize_results(results)

    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    base_name = f"{args.label}_{timestamp}"
    matches_path = os.path.join(args.output_dir, f"{base_name}_matches.csv")
    summary_path = os.path.join(args.output_dir, f"{base_name}_summary.csv")
    metadata_path = os.path.join(args.output_dir, f"{base_name}_metadata.json")

    with open(matches_path, "w", newline="", encoding="utf-8") as handle:
        fieldnames = ["ok", "mode", "position", "seed", "opponents", "win", "points", "rank", "error"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            row = dict(result)
            if isinstance(row.get("opponents"), list):
                row["opponents"] = "|".join(row["opponents"])
            writer.writerow(row)

    with open(summary_path, "w", newline="", encoding="utf-8") as handle:
        fieldnames = ["mode", "segment", "position", "games", "wins", "win_rate", "avg_points", "avg_rank", "errors"]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in summary_rows:
            writer.writerow(row)

    metadata = {
        "timestamp_started_utc": started_at,
        "timestamp_finished_utc": finished_at,
        "command": " ".join(sys.argv),
        "python_version": sys.version,
        "platform": platform.platform(),
        "git": repo_info,
        "arguments": vars(args),
        "artifacts": {
            "matches_csv": matches_path,
            "summary_csv": summary_path,
            "metadata_json": metadata_path,
        },
    }

    with open(metadata_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    print("Summary:")
    for row in summary_rows:
        print(
            f"mode={row['mode']} segment={row['segment']} position={row['position']} "
            f"win_rate={row['win_rate']:.3f} avg_points={row['avg_points']:.2f} avg_rank={row['avg_rank']:.2f} errors={row['errors']}"
        )

    print(f"Artifacts written to {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
