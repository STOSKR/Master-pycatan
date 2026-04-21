from __future__ import annotations

import csv
import json
import os
import statistics
import time
from pathlib import Path
from typing import Dict, List, Tuple

from PyCatan.benchmark_common import run_benchmark_vs_random, run_benchmark_vs_standard


AGENT_CLASS_PATH = "PyCatan.Agents.ShiyiHeuristicAgent.ShiyiHeuristicAgent"

ITERATIONS: List[Tuple[str, Dict[str, bool]]] = [
    (
        "iter0_random_baseline",
        {
            "on_game_start": False,
            "on_build_phase": False,
            "on_commerce_phase": False,
            "on_moving_thief": False,
        },
    ),
    (
        "iter1_game_start",
        {
            "on_game_start": True,
            "on_build_phase": False,
            "on_commerce_phase": False,
            "on_moving_thief": False,
        },
    ),
    (
        "iter2_build_phase",
        {
            "on_game_start": True,
            "on_build_phase": True,
            "on_commerce_phase": False,
            "on_moving_thief": False,
        },
    ),
    (
        "iter3_commerce_trade",
        {
            "on_game_start": True,
            "on_build_phase": True,
            "on_commerce_phase": True,
            "on_moving_thief": False,
        },
    ),
    (
        "iter4_thief_devcards",
        {
            "on_game_start": True,
            "on_build_phase": True,
            "on_commerce_phase": True,
            "on_moving_thief": True,
        },
    ),
]


def _ensure_defaults() -> None:
    os.environ.setdefault("CATAN_BENCH_SEEDS", "42,31415,2026")
    os.environ.setdefault("CATAN_BENCH_N_MATCHES", "25")
    os.environ.setdefault("CATAN_BENCH_N_MATCHES_PER_PERM", "5")
    os.environ.setdefault("CATAN_BENCH_MAX_PERMUTATIONS", "25")
    os.environ.setdefault("CATAN_BENCH_MAX_ROUNDS", "200")


def _set_iteration_agent(flags: Dict[str, bool]) -> None:
    os.environ["CATAN_BENCH_AGENTS"] = json.dumps(
        [{"class": AGENT_CLASS_PATH, "params": {"feature_flags": flags}}],
        ensure_ascii=True,
    )


def _compute_iteration_stats(rows: List[Dict[str, str]]) -> Dict[str, float]:
    winrates = [float(row["winrate"]) for row in rows]
    avg_winrate = statistics.mean(winrates) if winrates else 0.0
    std_winrate = statistics.pstdev(winrates) if len(winrates) > 1 else 0.0
    min_winrate = min(winrates) if winrates else 0.0
    return {
        "mean_winrate": avg_winrate,
        "std_winrate": std_winrate,
        "min_winrate": min_winrate,
    }


def _write_pipeline_summary(output_path: Path, summary_rows: List[Dict[str, str]]) -> None:
    fieldnames = [
        "iteration",
        "flags",
        "mean_winrate",
        "std_winrate",
        "min_winrate",
        "gate_70",
    ]
    with output_path.open(mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)


if __name__ == "__main__":
    _ensure_defaults()
    start = time.time()

    pipeline_summary: List[Dict[str, str]] = []
    gate_iteration: Tuple[str, Dict[str, bool]] | None = None

    for iteration_name, flags in ITERATIONS:
        print(f"\n=== {iteration_name} ===")
        _set_iteration_agent(flags)
        rows, output_path = run_benchmark_vs_random(
            output_filename=f"{iteration_name}_benchmark_vs_random_resultados.csv"
        )
        stats = _compute_iteration_stats(rows)
        gate_70 = stats["mean_winrate"] >= 0.70
        if gate_70 and gate_iteration is None:
            gate_iteration = (iteration_name, flags)

        print(
            f"{iteration_name}: mean={stats['mean_winrate']:.2%} "
            f"std={stats['std_winrate']:.2%} min={stats['min_winrate']:.2%} | gate70={gate_70}"
        )
        print(f"CSV: {output_path}")

        pipeline_summary.append(
            {
                "iteration": iteration_name,
                "flags": json.dumps(flags, ensure_ascii=True, sort_keys=True),
                "mean_winrate": f"{stats['mean_winrate']:.4f}",
                "std_winrate": f"{stats['std_winrate']:.4f}",
                "min_winrate": f"{stats['min_winrate']:.4f}",
                "gate_70": str(gate_70),
            }
        )

    base_dir = Path(__file__).resolve().parent
    summary_path = base_dir / "benchmark_iterative_summary.csv"
    _write_pipeline_summary(summary_path, pipeline_summary)
    print(f"\nResumen iterativo guardado en: {summary_path}")

    if gate_iteration is not None:
        iteration_name, flags = gate_iteration
        print(f"\nGate >=70% alcanzado en {iteration_name}. Ejecutando benchmark vs estándar...")
        _set_iteration_agent(flags)
        rows, output_path = run_benchmark_vs_standard(
            output_filename=f"{iteration_name}_benchmark_vs_estandar_resultados.csv"
        )
        print(f"CSV estándar guardado en: {output_path}")
        for row in rows:
            print(
                f"{row['agent_name']} | seed={row['seed']} | winrate={float(row['winrate']):.2%} "
                f"({row['wins']}/{row['matches']})"
            )
    else:
        print("\nNo se alcanzó el gate de 70% en las iteraciones definidas.")

    elapsed = int(time.time() - start)
    hours, rem = divmod(elapsed, 3600)
    minutes, seconds = divmod(rem, 60)
    print(f"\nTiempo total pipeline: {hours}h {minutes}m {seconds}s")
