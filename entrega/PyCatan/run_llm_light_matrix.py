from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from PyCatan.benchmark_common import (
    load_repo_env_file,
    run_benchmark_vs_random,
    run_benchmark_vs_standard,
)


LLM_AGENT_PATH = "PyCatan.Agents.ShiyiLLMAgent.ShiyiLLMAgent"
DEFAULT_PROMPTS = ["compact_json"]
DEFAULT_OLLAMA_MODELS: List[str] = []
DEFAULT_UPV_MODELS: List[str] = []
DEFAULT_BEDROCK_MODELS: List[str] = []


def _parse_csv_env(name: str, defaults: Sequence[str]) -> List[str]:
    raw = os.getenv(name, "").strip()
    if not raw:
        return list(defaults)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _ensure_light_defaults() -> None:
    os.environ.setdefault("CATAN_BENCH_SEEDS", "42")
    os.environ.setdefault("CATAN_BENCH_N_MATCHES", "25")
    os.environ.setdefault("CATAN_BENCH_N_MATCHES_PER_PERM", "1")
    os.environ.setdefault("CATAN_BENCH_MAX_PERMUTATIONS", "25")
    os.environ.setdefault("CATAN_BENCH_MAX_ROUNDS", "200")
    os.environ.setdefault("CATAN_BENCH_WORKERS_PCT", "0.01")
    os.environ.setdefault("CATAN_LLM_DECISION_TIMEOUT_SECONDS", "90")
    os.environ.setdefault("CATAN_LLM_ABORT_ON_FALLBACK", "1")


def _set_llm_agent(prompt_variant: str) -> None:
    timeout_seconds = float(os.getenv("CATAN_LLM_DECISION_TIMEOUT_SECONDS", "90"))
    llm_config = {
        "enable_on_game_start": True,
        "enable_on_build_phase": True,
        "prompt_variant_on_game_start": prompt_variant,
        "prompt_variant_on_build_phase": prompt_variant,
        "decision_timeout_seconds": timeout_seconds,
    }
    os.environ["CATAN_BENCH_AGENTS"] = json.dumps(
        [{"class": LLM_AGENT_PATH, "params": {"llm_config": llm_config}}],
        ensure_ascii=True,
    )


def _sanitize(text: str) -> str:
    return (
        text.replace(":", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(".", "_")
        .replace(" ", "_")
    )


def _model_size_score(model: str) -> float:
    match = re.search(r"(\d+(?:\.\d+)?)\s*b\b", model, flags=re.IGNORECASE)
    if match:
        return float(match.group(1))
    return 9999.0


def _detect_ollama_models() -> List[str]:
    try:
        completed = subprocess.run(
            ["ollama", "list"],
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except Exception:
        return []

    if completed.returncode != 0:
        return []

    models: List[str] = []
    for raw_line in completed.stdout.splitlines():
        line = raw_line.strip()
        if not line or line.upper().startswith("NAME"):
            continue
        models.append(line.split()[0])

    return sorted(models, key=lambda item: (_model_size_score(item), item))


def _provider_model_pairs() -> List[Tuple[str, str]]:
    providers = _parse_csv_env("CATAN_LLM_PROVIDERS", ["ollama"])
    configs: List[Tuple[str, str]] = []

    for provider in providers:
        if provider == "ollama":
            detected_models = _detect_ollama_models()
            models = _parse_csv_env(
                "CATAN_LLM_OLLAMA_MODELS",
                detected_models or DEFAULT_OLLAMA_MODELS,
            )
            models = sorted(models, key=lambda item: (_model_size_score(item), item))
        elif provider == "upv":
            models = _parse_csv_env("CATAN_LLM_UPV_MODELS", DEFAULT_UPV_MODELS)
        elif provider == "bedrock":
            models = _parse_csv_env("CATAN_LLM_BEDROCK_MODELS", DEFAULT_BEDROCK_MODELS)
        else:
            continue

        configs.extend((provider, model) for model in models)

    return configs


def _assert_no_fallback(rows: Sequence[Dict[str, str]], context: str) -> None:
    fallback_rows = [
        row
        for row in rows
        if int(row.get("fallback_count") or 0) > 0
    ]
    if not fallback_rows:
        return

    details = "; ".join(
        (
            f"seed={row.get('seed')} matches={row.get('matches')} "
            f"fallback_count={row.get('fallback_count')} "
            f"fallback_rate={row.get('fallback_rate')}"
        )
        for row in fallback_rows
    )
    raise RuntimeError(f"Fallback detected in {context}: {details}")


def _summary_row(
    row: Dict[str, str],
    provider: str,
    model: str,
    prompt: str,
    benchmark: str,
) -> Dict[str, str]:
    return {
        "provider": provider,
        "model": model,
        "prompt_variant": prompt,
        "benchmark_type": benchmark,
        "seed": str(row["seed"]),
        "matches": str(row["matches"]),
        "wins": str(row["wins"]),
        "winrate": str(row["winrate"]),
        "avg_points": str(row["avg_points"]),
        "avg_rank": str(row["avg_rank"]),
        "llm_decisions": str(row["llm_decisions"]),
        "fallback_count": str(row["fallback_count"]),
        "fallback_rate": str(row["fallback_rate"]),
        "latency_ms_total": str(row["latency_ms_total"]),
        "avg_latency_ms": str(row["avg_latency_ms"]),
        "input_tokens_total": str(row["input_tokens_total"]),
        "output_tokens_total": str(row["output_tokens_total"]),
        "token_decisions": str(row["token_decisions"]),
        "avg_input_tokens": str(row["avg_input_tokens"]),
        "avg_output_tokens": str(row["avg_output_tokens"]),
    }


if __name__ == "__main__":
    load_repo_env_file()
    _ensure_light_defaults()

    prompts = _parse_csv_env("CATAN_LLM_PROMPT_VARIANTS", DEFAULT_PROMPTS)
    provider_model_pairs = _provider_model_pairs()
    if not provider_model_pairs:
        print(
            "No hay configuraciones LLM activas. Define CATAN_LLM_PROVIDERS y al menos una "
            "lista de modelos, por ejemplo CATAN_LLM_OLLAMA_MODELS=llama3.2:1b."
        )
        raise SystemExit(1)

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_rel = Path("results") / "llm_light" / run_id
    base_abs = Path(__file__).resolve().parent / base_rel
    base_abs.mkdir(parents=True, exist_ok=True)

    metadata = {
        "run_id": run_id,
        "providers": sorted({provider for provider, _ in provider_model_pairs}),
        "models": [model for _, model in provider_model_pairs],
        "prompts": prompts,
        "seeds": os.getenv("CATAN_BENCH_SEEDS", ""),
        "n_matches_random": os.getenv("CATAN_BENCH_N_MATCHES", ""),
        "n_matches_per_perm_standard": os.getenv("CATAN_BENCH_N_MATCHES_PER_PERM", ""),
        "max_permutations_standard": os.getenv("CATAN_BENCH_MAX_PERMUTATIONS", ""),
        "max_rounds": os.getenv("CATAN_BENCH_MAX_ROUNDS", ""),
        "workers_pct": os.getenv("CATAN_BENCH_WORKERS_PCT", ""),
        "decision_timeout_seconds": os.getenv("CATAN_LLM_DECISION_TIMEOUT_SECONDS", ""),
        "abort_on_fallback": os.getenv("CATAN_LLM_ABORT_ON_FALLBACK", ""),
        "started_at": datetime.now().isoformat(timespec="seconds"),
    }
    (base_abs / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    summary_rows: List[Dict[str, str]] = []
    start = time.time()

    for provider, model in provider_model_pairs:
        os.environ["CATAN_LLM_PROVIDER"] = provider
        os.environ["CATAN_LLM_MODEL"] = model

        for prompt in prompts:
            _set_llm_agent(prompt)

            model_dir = f"provider_{_sanitize(provider)}__model_{_sanitize(model)}"
            prompt_dir = f"prompt_{_sanitize(prompt)}"

            random_rel = base_rel / model_dir / prompt_dir / "vs_random.csv"
            standard_rel = base_rel / model_dir / prompt_dir / "vs_standard.csv"

            print(f"\n[{provider}] model={model} prompt={prompt} -> vs_random")
            random_rows, random_path = run_benchmark_vs_random(
                output_filename=str(random_rel).replace("\\", "/")
            )
            print(f"CSV vs_random: {random_path}")
            if os.getenv("CATAN_LLM_ABORT_ON_FALLBACK", "1") == "1":
                _assert_no_fallback(random_rows, f"{provider}/{model}/{prompt}/vs_random")

            print(f"[{provider}] model={model} prompt={prompt} -> vs_standard")
            standard_rows, standard_path = run_benchmark_vs_standard(
                output_filename=str(standard_rel).replace("\\", "/")
            )
            print(f"CSV vs_standard: {standard_path}")
            if os.getenv("CATAN_LLM_ABORT_ON_FALLBACK", "1") == "1":
                _assert_no_fallback(standard_rows, f"{provider}/{model}/{prompt}/vs_standard")

            for row in random_rows:
                summary_row = _summary_row(row, provider, model, prompt, "vs_random")
                summary_row["result_csv"] = str(random_path)
                summary_rows.append(summary_row)

            for row in standard_rows:
                summary_row = _summary_row(row, provider, model, prompt, "vs_standard")
                summary_row["result_csv"] = str(standard_path)
                summary_rows.append(summary_row)

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
                "llm_decisions",
                "fallback_count",
                "fallback_rate",
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
    print(f"\nResumen guardado en: {summary_path}")
    print(f"Carpeta de resultados: {base_abs}")
    print(f"Tiempo total: {hours}h {minutes}m {seconds}s")
