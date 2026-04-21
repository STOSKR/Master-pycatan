from __future__ import annotations

import csv
import json
import os
import time
from pathlib import Path
from typing import Dict, List, Tuple

from PyCatan.benchmark_common import run_benchmark_vs_random


LLM_AGENT_PATH = "PyCatan.Agents.ShiyiLLMAgent.ShiyiLLMAgent"


def _parse_csv_env(name: str, default: str = "") -> List[str]:
    raw = os.getenv(name, default).strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _ensure_light_defaults() -> None:
    os.environ.setdefault("CATAN_BENCH_SEEDS", "42")
    os.environ.setdefault("CATAN_BENCH_N_MATCHES", "8")
    os.environ.setdefault("CATAN_BENCH_MAX_ROUNDS", "200")


def _build_configs() -> List[Tuple[str, str, str]]:
    prompt_variants = _parse_csv_env(
        "CATAN_LLM_PROMPT_VARIANTS", "compact_json,resource_focus,safe_legal"
    )
    upv_models = _parse_csv_env("CATAN_LLM_UPV_MODELS")
    bedrock_models = _parse_csv_env("CATAN_LLM_BEDROCK_MODELS")

    configs: List[Tuple[str, str, str]] = []
    for model in upv_models:
        for prompt in prompt_variants:
            configs.append(("upv", model, prompt))
    for model in bedrock_models:
        for prompt in prompt_variants:
            configs.append(("bedrock", model, prompt))
    return configs


def _set_llm_agent(prompt_variant: str) -> None:
    llm_config = {
        "enable_on_game_start": True,
        "enable_on_build_phase": True,
        "prompt_variant_on_game_start": prompt_variant,
        "prompt_variant_on_build_phase": prompt_variant,
    }
    os.environ["CATAN_BENCH_AGENTS"] = json.dumps(
        [{"class": LLM_AGENT_PATH, "params": {"llm_config": llm_config}}],
        ensure_ascii=True,
    )


if __name__ == "__main__":
    _ensure_light_defaults()
    start = time.time()

    configs = _build_configs()
    if len(configs) < 3:
        print(
            "Configuraciones insuficientes. Define CATAN_LLM_UPV_MODELS y "
            "CATAN_LLM_BEDROCK_MODELS con al menos 3 modelos en total."
        )
        raise SystemExit(1)

    all_rows: List[Dict[str, str]] = []

    for provider, model, prompt_variant in configs:
        os.environ["CATAN_LLM_PROVIDER"] = provider
        os.environ["CATAN_LLM_MODEL"] = model
        _set_llm_agent(prompt_variant)

        output_filename = (
            f"llm_phase2_{provider}_{model.replace(':', '_').replace('.', '_')}_{prompt_variant}.csv"
        )
        print(f"\nEvaluando provider={provider} model={model} prompt={prompt_variant}")
        rows, output_path = run_benchmark_vs_random(output_filename=output_filename)
        print(f"CSV: {output_path}")

        for row in rows:
            all_rows.append(
                {
                    "provider": provider,
                    "model": model,
                    "prompt_variant": prompt_variant,
                    "seed": str(row["seed"]),
                    "matches": str(row["matches"]),
                    "wins": str(row["wins"]),
                    "winrate": str(row["winrate"]),
                    "avg_points": str(row["avg_points"]),
                    "avg_rank": str(row["avg_rank"]),
                    "fallback_rate": str(row["fallback_rate"]),
                    "llm_decisions": str(row["llm_decisions"]),
                }
            )

    summary_path = Path(__file__).resolve().parent / "llm_phase2_summary.csv"
    with summary_path.open(mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "provider",
                "model",
                "prompt_variant",
                "seed",
                "matches",
                "wins",
                "winrate",
                "avg_points",
                "avg_rank",
                "fallback_rate",
                "llm_decisions",
            ],
        )
        writer.writeheader()
        writer.writerows(all_rows)

    elapsed = int(time.time() - start)
    hours, rem = divmod(elapsed, 3600)
    minutes, seconds = divmod(rem, 60)
    print(f"\nResumen LLM guardado en: {summary_path}")
    print(f"Tiempo total: {hours}h {minutes}m {seconds}s")
