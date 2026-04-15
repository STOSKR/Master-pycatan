from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
from pathlib import Path
import random
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# Allow running this script directly from the experiments folder.
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from PyCatan.Agents.AlexPelochoJaimeLLMAgent import (
    AlexPelochoJaimeLLMAgent,
    LLMBehaviorConfig,
)
from PyCatan.Agents.RandomAgent import RandomAgent
from PyCatan.Agents.llm_engine import (
    BaseLLMProvider,
    BedrockProvider,
    OllamaProvider,
    ProviderError,
    UPVProvider,
)
from PyCatan.Managers.GameDirector import GameDirector


def parse_match_result(trace: Dict, position: int) -> Tuple[int, int, int]:
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

    return win, points, rank


def build_provider(provider_name: str, model: str) -> BaseLLMProvider:
    provider_name = provider_name.strip().lower()
    if provider_name == "ollama":
        base_url = os.getenv("CATAN_OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        return OllamaProvider(model=model, base_url=base_url)

    if provider_name == "bedrock":
        region = os.getenv("CATAN_BEDROCK_REGION", "eu-west-1")
        return BedrockProvider(model=model, region_name=region)

    if provider_name == "upv":
        endpoint = os.getenv("CATAN_UPV_CHAT_ENDPOINT", "").strip()
        api_key = os.getenv("CATAN_UPV_API_KEY", "").strip()
        if not endpoint or not api_key:
            raise ProviderError("UPV requires CATAN_UPV_CHAT_ENDPOINT and CATAN_UPV_API_KEY")
        return UPVProvider(model=model, chat_endpoint=endpoint, api_key=api_key)

    raise ProviderError(f"Unsupported provider: {provider_name}")


def run_single_game(
    provider: BaseLLMProvider,
    prompt_variant: str,
    position: int,
    seed: int,
    max_rounds: int,
) -> Dict:
    random.seed(seed)

    class ConfiguredAgent(AlexPelochoJaimeLLMAgent):
        def __init__(self, agent_id):
            super().__init__(
                agent_id=agent_id,
                llm_config=LLMBehaviorConfig(
                    enable_on_game_start=True,
                    enable_on_build_phase=True,
                    prompt_variant_on_game_start=prompt_variant,
                    prompt_variant_on_build_phase=prompt_variant,
                    max_actions_on_game_start=14,
                    max_actions_on_build_phase=14,
                    decision_timeout_seconds=8.0,
                ),
                provider=provider,
            )

    agents = [RandomAgent, RandomAgent, RandomAgent]
    agents.insert(position, ConfiguredAgent)

    game_director = GameDirector(agents=agents, max_rounds=max_rounds, store_trace=False)
    trace = game_director.game_start(print_outcome=False)

    win, points, rank = parse_match_result(trace, position)
    agent_obj = game_director.game_manager.agent_manager.players[position]["player"]
    decision_history = agent_obj.get_llm_decision_history()

    decisions = len(decision_history)
    fallback_count = sum(1 for decision in decision_history if decision.get("fallback"))
    mean_latency = (
        sum(decision.get("latency_ms", 0) for decision in decision_history) / decisions
        if decisions
        else 0.0
    )

    return {
        "win": win,
        "points": points,
        "rank": rank,
        "decisions": decisions,
        "fallback_count": fallback_count,
        "mean_latency_ms": round(mean_latency, 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Lightweight LLM evaluation for Catan agent decisions")
    parser.add_argument(
        "--model-config",
        action="append",
        help="Provider/model pair as provider=model. Repeat for multiple models.",
    )
    parser.add_argument(
        "--prompt-variants",
        default="compact_json,resource_focus,safe_legal",
        help="Comma-separated prompt variants.",
    )
    parser.add_argument("--games-per-config", type=int, default=8)
    parser.add_argument("--max-rounds", type=int, default=120)
    parser.add_argument("--seed", type=int, default=77)
    parser.add_argument("--output-dir", default="experiments/results")
    parser.add_argument("--label", default="llm_light")
    args = parser.parse_args()

    model_configs = args.model_config or [
        "ollama=llama3.1:8b",
        "bedrock=anthropic.claude-3-haiku-20240307-v1:0",
        "upv=gpt-4o-mini",
    ]

    prompt_variants = [item.strip() for item in args.prompt_variants.split(",") if item.strip()]

    os.makedirs(args.output_dir, exist_ok=True)

    rows: List[Dict] = []
    started_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    for model_entry in model_configs:
        if "=" not in model_entry:
            rows.append(
                {
                    "provider": "invalid",
                    "model": model_entry,
                    "prompt_variant": "n/a",
                    "status": "error",
                    "error": "invalid model-config format (expected provider=model)",
                }
            )
            continue

        provider_name, model_name = model_entry.split("=", 1)

        try:
            provider = build_provider(provider_name, model_name)
        except Exception as exc:
            for prompt_variant in prompt_variants:
                rows.append(
                    {
                        "provider": provider_name,
                        "model": model_name,
                        "prompt_variant": prompt_variant,
                        "status": "error",
                        "error": repr(exc),
                    }
                )
            continue

        for prompt_variant in prompt_variants:
            game_rows = []
            errors = []

            for game_idx in range(args.games_per_config):
                position = game_idx % 4
                seed = args.seed + game_idx + hash((provider_name, model_name, prompt_variant)) % 100_000
                try:
                    result = run_single_game(
                        provider=provider,
                        prompt_variant=prompt_variant,
                        position=position,
                        seed=seed,
                        max_rounds=args.max_rounds,
                    )
                    game_rows.append(result)
                except Exception as exc:
                    errors.append(repr(exc))

            if not game_rows:
                rows.append(
                    {
                        "provider": provider_name,
                        "model": model_name,
                        "prompt_variant": prompt_variant,
                        "status": "error",
                        "games": 0,
                        "wins": 0,
                        "win_rate": 0.0,
                        "avg_points": 0.0,
                        "avg_rank": 0.0,
                        "avg_decisions": 0.0,
                        "fallback_rate": 0.0,
                        "avg_latency_ms": 0.0,
                        "error": " | ".join(errors[:3]),
                    }
                )
                continue

            total_games = len(game_rows)
            wins = sum(row["win"] for row in game_rows)
            decisions = sum(row["decisions"] for row in game_rows)
            fallback_count = sum(row["fallback_count"] for row in game_rows)

            rows.append(
                {
                    "provider": provider_name,
                    "model": model_name,
                    "prompt_variant": prompt_variant,
                    "status": "ok" if not errors else "partial",
                    "games": total_games,
                    "wins": wins,
                    "win_rate": wins / total_games,
                    "avg_points": sum(row["points"] for row in game_rows) / total_games,
                    "avg_rank": sum(row["rank"] for row in game_rows) / total_games,
                    "avg_decisions": decisions / total_games,
                    "fallback_rate": (fallback_count / decisions) if decisions else 0.0,
                    "avg_latency_ms": sum(row["mean_latency_ms"] for row in game_rows) / total_games,
                    "error": " | ".join(errors[:3]),
                }
            )

    finished_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
    base_name = f"{args.label}_{timestamp}"
    summary_path = os.path.join(args.output_dir, f"{base_name}_summary.csv")
    metadata_path = os.path.join(args.output_dir, f"{base_name}_metadata.json")

    with open(summary_path, "w", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "provider",
            "model",
            "prompt_variant",
            "status",
            "games",
            "wins",
            "win_rate",
            "avg_points",
            "avg_rank",
            "avg_decisions",
            "fallback_rate",
            "avg_latency_ms",
            "error",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)

    metadata = {
        "timestamp_started_utc": started_at,
        "timestamp_finished_utc": finished_at,
        "command": " ".join(sys.argv),
        "arguments": vars(args),
        "artifact": {"summary_csv": summary_path, "metadata_json": metadata_path},
    }

    with open(metadata_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    print(f"Summary written to {summary_path}")
    for row in rows:
        if row.get("status") in ("ok", "partial"):
            print(
                f"{row['provider']} {row['model']} {row['prompt_variant']} "
                f"win_rate={row['win_rate']:.3f} avg_points={row['avg_points']:.2f} "
                f"avg_rank={row['avg_rank']:.2f} fallback_rate={row['fallback_rate']:.3f}"
            )
        else:
            print(f"{row['provider']} {row['model']} {row['prompt_variant']} ERROR: {row.get('error', '')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
