from __future__ import annotations

import csv
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from PyCatan.benchmark_common import (
    load_repo_env_file,
    run_benchmark_vs_random,
    run_benchmark_vs_standard,
)


LLM_AGENT_PATH = "PyCatan.Agents.ShiyiLLMAgent.ShiyiLLMAgent"
DEFAULT_PROMPTS = ["compact_json", "resource_focus", "safe_legal"]
DEFAULT_MODELS = ["us.amazon.nova-micro-v1:0"]
DEFAULT_REGION = "us-west-2"


def _parse_csv_env(name: str, defaults: List[str]) -> List[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return list(defaults)
    return [item.strip() for item in raw.split(",") if item.strip()]


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


def _ensure_default_budgets() -> None:
    os.environ.setdefault("CATAN_BENCH_SEEDS", "42")
    os.environ.setdefault("CATAN_BENCH_N_MATCHES", "8")
    os.environ.setdefault("CATAN_BENCH_N_MATCHES_PER_PERM", "2")
    os.environ.setdefault("CATAN_BENCH_MAX_PERMUTATIONS", "10")
    os.environ.setdefault("CATAN_BENCH_MAX_ROUNDS", "200")


def _sanitize(text: str) -> str:
    return (
        text.replace(":", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(".", "_")
        .replace(" ", "_")
    )


def _validate_env() -> List[str]:
    missing: List[str] = []
    if not os.getenv("CATAN_AWS_ACCESS_KEY", "").strip():
        missing.append("CATAN_AWS_ACCESS_KEY")
    return missing


def _summary_row(
    row: Dict[str, str],
    provider: str,
    model: str,
    prompt: str,
    benchmark_type: str,
    result_csv: str,
) -> Dict[str, str]:
    return {
        "provider": provider,
        "model": model,
        "prompt_variant": prompt,
        "benchmark_type": benchmark_type,
        "seed": str(row["seed"]),
        "matches": str(row["matches"]),
        "wins": str(row["wins"]),
        "winrate": str(row["winrate"]),
        "avg_points": str(row["avg_points"]),
        "avg_rank": str(row["avg_rank"]),
        "fallback_rate": str(row["fallback_rate"]),
        "llm_decisions": str(row["llm_decisions"]),
        "latency_ms_total": str(row["latency_ms_total"]),
        "avg_latency_ms": str(row["avg_latency_ms"]),
        "input_tokens_total": str(row["input_tokens_total"]),
        "output_tokens_total": str(row["output_tokens_total"]),
        "token_decisions": str(row["token_decisions"]),
        "avg_input_tokens": str(row["avg_input_tokens"]),
        "avg_output_tokens": str(row["avg_output_tokens"]),
        "result_csv": result_csv,
    }


if __name__ == "__main__":
    load_repo_env_file()
    _ensure_default_budgets()

    missing = _validate_env()
    if missing:
        print("Faltan variables para Bedrock: " + ", ".join(missing))
        raise SystemExit(1)

    os.environ.setdefault("CATAN_BEDROCK_REGION", DEFAULT_REGION)
    os.environ["CATAN_LLM_PROVIDER"] = "bedrock"

    prompts = _parse_csv_env("CATAN_LLM_PROMPT_VARIANTS", DEFAULT_PROMPTS)
    models = _parse_csv_env("CATAN_LLM_BEDROCK_MODELS", DEFAULT_MODELS)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_rel = Path("results") / "bedrock_llm" / run_id
    base_abs = Path(__file__).resolve().parent / base_rel
    base_abs.mkdir(parents=True, exist_ok=True)

    metadata = {
        "run_id": run_id,
        "provider": "bedrock",
        "region": os.getenv("CATAN_BEDROCK_REGION", ""),
        "prompts": prompts,
        "models": models,
        "seeds": os.getenv("CATAN_BENCH_SEEDS", ""),
        "n_matches_random": os.getenv("CATAN_BENCH_N_MATCHES", ""),
        "n_matches_per_perm_standard": os.getenv("CATAN_BENCH_N_MATCHES_PER_PERM", ""),
        "max_permutations_standard": os.getenv("CATAN_BENCH_MAX_PERMUTATIONS", ""),
        "max_rounds": os.getenv("CATAN_BENCH_MAX_ROUNDS", ""),
        "started_at": datetime.now().isoformat(timespec="seconds"),
    }
    (base_abs / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    summary_rows: List[Dict[str, str]] = []
    start = time.time()

    for model in models:
        os.environ["CATAN_LLM_MODEL"] = model

        for prompt in prompts:
            _set_llm_agent(prompt)

            model_dir = f"model_{_sanitize(model)}"
            prompt_dir = f"prompt_{_sanitize(prompt)}"

            random_rel = base_rel / model_dir / prompt_dir / "vs_random.csv"
            standard_rel = base_rel / model_dir / prompt_dir / "vs_standard.csv"

            print(f"\n[Bedrock] model={model} prompt={prompt} -> vs_random")
            random_rows, random_path = run_benchmark_vs_random(
                output_filename=str(random_rel).replace("\\", "/")
            )
            print(f"CSV vs_random: {random_path}")

            print(f"[Bedrock] model={model} prompt={prompt} -> vs_standard")
            standard_rows, standard_path = run_benchmark_vs_standard(
                output_filename=str(standard_rel).replace("\\", "/")
            )
            print(f"CSV vs_standard: {standard_path}")

            for row in random_rows:
                summary_rows.append(
                    _summary_row(row, "bedrock", model, prompt, "vs_random", str(random_path))
                )

            for row in standard_rows:
                summary_rows.append(
                    _summary_row(
                        row,
                        "bedrock",
                        model,
                        prompt,
                        "vs_standard",
                        str(standard_path),
                    )
                )

    summary_path = base_abs / "summary.csv"
    with summary_path.open(mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "provider",
                "model",
                "prompt_variant",
                "benchmark_type",
                "seed",
                "matches",
                "wins",
                "winrate",
                "avg_points",
                "avg_rank",
                "fallback_rate",
                "llm_decisions",
                "latency_ms_total",
                "avg_latency_ms",
                "input_tokens_total",
                "output_tokens_total",
                "token_decisions",
                "avg_input_tokens",
                "avg_output_tokens",
                "result_csv",
            ],
        )
        writer.writeheader()
        writer.writerows(summary_rows)

    elapsed = int(time.time() - start)
    hours, rem = divmod(elapsed, 3600)
    minutes, seconds = divmod(rem, 60)
    print(f"\nResumen global guardado en: {summary_path}")
    print(f"Carpeta de resultados: {base_abs}")
    print(f"Tiempo total: {hours}h {minutes}m {seconds}s")
