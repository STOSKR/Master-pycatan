from __future__ import annotations

import time

from PyCatan.benchmark_common import run_benchmark_vs_standard


if __name__ == "__main__":
    start_time = time.time()
    rows, output_path = run_benchmark_vs_standard()
    print(f"\nResultados guardados en: {output_path}")
    for row in rows:
        print(
            f"{row['agent_name']} | seed={row['seed']} | winrate={float(row['winrate']):.2%} "
            f"({row['wins']}/{row['matches']}) | avg_points={row['avg_points']} | avg_rank={row['avg_rank']}"
        )

    elapsed = int(time.time() - start_time)
    hours, rem = divmod(elapsed, 3600)
    minutes, seconds = divmod(rem, 60)
    print(f"\nTiempo total: {hours}h {minutes}m {seconds}s")
