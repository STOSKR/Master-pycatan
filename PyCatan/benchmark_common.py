from __future__ import annotations

import concurrent.futures
import csv
import hashlib
import importlib
import inspect
import itertools
import json
import os
import random
import traceback
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from PyCatan.Interfaces.AgentInterface import AgentInterface as AgIn
from PyCatan.Managers.GameDirector import GameDirector


DEFAULT_AGENT_SPECS: List[Tuple[str, Optional[Any]]] = [
    ("PyCatan.Agents.ShiyiHeuristicAgent.ShiyiHeuristicAgent", None),
    ("PyCatan.Agents.ShiyiLLMAgent.ShiyiLLMAgent", None),
]

STANDARD_AGENT_PATHS: List[str] = [
    "PyCatan.Agents.RandomAgent.RandomAgent",
    "PyCatan.Agents.AdrianHerasAgent.AdrianHerasAgent",
    "PyCatan.Agents.AlexPastorAgent.AlexPastorAgent",
    "PyCatan.Agents.AlexPelochoJaimeAgent.AlexPelochoJaimeAgent",
    "PyCatan.Agents.CarlesZaidaAgent.CarlesZaidaAgent",
    "PyCatan.Agents.CrabisaAgent.CrabisaAgent",
    "PyCatan.Agents.EdoAgent.EdoAgent",
    "PyCatan.Agents.PabloAleixAlexAgent.PabloAleixAlexAgent",
    "PyCatan.Agents.SigmaAgent.SigmaAgent",
    "PyCatan.Agents.TristanAgent.TristanAgent",
]

BENCHMARK_SUMMARY_FIELDS = [
    "agent_path",
    "agent_name",
    "benchmark_type",
    "seed",
    "matches",
    "wins",
    "winrate",
    "points_total",
    "avg_points",
    "avg_rank",
    "llm_decisions",
    "fallback_count",
    "fallback_rate",
    "provider",
    "model",
]


def load_repo_env_file() -> None:
    """Loads .env from repository root if present (without overriding existing env vars)."""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")

    # Aliases for compatibility (API_UPV can be either endpoint base URL or API key).
    api_upv = os.getenv("API_UPV", "").strip()
    if api_upv:
        if api_upv.lower().startswith("http://") or api_upv.lower().startswith("https://"):
            if "CATAN_UPV_CHAT_ENDPOINT" not in os.environ:
                endpoint = api_upv.rstrip("/")
                if not endpoint.endswith("/chat/completions"):
                    endpoint = endpoint + "/chat/completions"
                os.environ["CATAN_UPV_CHAT_ENDPOINT"] = endpoint
        elif "CATAN_UPV_API_KEY" not in os.environ:
            os.environ["CATAN_UPV_API_KEY"] = api_upv

    # AWS mapping is handled inside llm_engine (supports both bearer and classic creds).


def load_agent_class(class_path: str):
    module_name, class_name = class_path.rsplit(".", 1)
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def create_agent_class_with_dict_params(agent_class, **kwargs):
    class ConfiguredAgent(agent_class):
        def __init__(self, agent_id):
            super().__init__(agent_id, **kwargs)

    ConfiguredAgent.__name__ = f"{agent_class.__name__}_ConfiguredDict"
    return ConfiguredAgent


def create_agent_class_with_list_params(agent_class, params_list):
    class ConfiguredAgent(agent_class):
        def __init__(self, agent_id):
            super().__init__(agent_id, *params_list)

    ConfiguredAgent.__name__ = f"{agent_class.__name__}_ConfiguredList"
    return ConfiguredAgent


def parse_seeds() -> List[int]:
    seeds_from_list = os.getenv("CATAN_BENCH_SEEDS", "").strip()
    if seeds_from_list:
        raw_values = [item.strip() for item in seeds_from_list.split(",") if item.strip()]
        if raw_values:
            return [int(item) for item in raw_values]

    single_seed = os.getenv("CATAN_BENCH_RANDOM_SEED", "").strip()
    if single_seed:
        return [int(single_seed)]

    return [42, 31415, 2026]


def parse_agent_specs() -> List[Tuple[str, Optional[Any]]]:
    raw_json = os.getenv("CATAN_BENCH_AGENTS", "").strip()
    if not raw_json:
        return list(DEFAULT_AGENT_SPECS)

    try:
        decoded = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "CATAN_BENCH_AGENTS must be valid JSON. "
            'Example: [{"class":"PyCatan.Agents.MyAgent.MyAgent","params":null}]'
        ) from exc

    if not isinstance(decoded, list):
        raise ValueError("CATAN_BENCH_AGENTS must decode to a list")

    parsed: List[Tuple[str, Optional[Any]]] = []
    for item in decoded:
        if isinstance(item, str):
            parsed.append((item, None))
            continue

        if not isinstance(item, dict):
            raise ValueError("Each CATAN_BENCH_AGENTS item must be a string or object")

        class_path = item.get("class")
        if not isinstance(class_path, str) or not class_path:
            raise ValueError('Each object item must include a non-empty "class" string')
        parsed.append((class_path, item.get("params")))

    if not parsed:
        raise ValueError("CATAN_BENCH_AGENTS produced an empty list")
    return parsed


def parse_worker_count() -> int:
    pct = float(os.getenv("CATAN_BENCH_WORKERS_PCT", "0.95"))
    total_workers = os.cpu_count() or 1
    return max(1, int(total_workers * pct))


def create_parallel_executor(max_workers: int):
    try:
        return concurrent.futures.ProcessPoolExecutor(max_workers=max_workers)
    except Exception as exc:
        print(
            "ProcessPoolExecutor no disponible en este entorno "
            f"({type(exc).__name__}: {exc}). Se usa ThreadPoolExecutor."
        )
        return concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)


def stable_match_seed(*parts: Any) -> int:
    payload = "::".join(str(part) for part in parts).encode("utf-8")
    digest = hashlib.sha256(payload).digest()
    return int.from_bytes(digest[:4], byteorder="big", signed=False)


def agent_identifier(agent_path: str, params: Optional[Any]) -> str:
    if params is None:
        return agent_path
    encoded = json.dumps(params, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return f"{agent_path}::{encoded}"


def safe_agent_name(agent_path: str) -> str:
    return agent_path.rsplit(".", 1)[-1]


def build_agent_class(agent_class, params: Optional[Any]):
    if params is None:
        return agent_class
    if isinstance(params, (list, tuple)):
        return create_agent_class_with_list_params(agent_class, params)
    if isinstance(params, dict):
        return create_agent_class_with_dict_params(agent_class, **params)
    raise TypeError("params must be list/tuple/dict or null")


def extract_match_outcome(game_director: GameDirector, position: int):
    game_trace = game_director.game_start(print_outcome=False)

    last_round = max(game_trace["game"].keys(), key=lambda r: int(r.split("_")[-1]))
    last_turn = max(
        game_trace["game"][last_round].keys(),
        key=lambda t: int(t.split("_")[-1].lstrip("P")),
    )
    victory_points = game_trace["game"][last_round][last_turn]["end_turn"]["victory_points"]

    agent_id = f"J{position}"
    points = int(victory_points[agent_id])
    winner = max(victory_points, key=lambda player: int(victory_points[player]))
    victory = 1 if winner == agent_id else 0

    ordered = sorted(victory_points.items(), key=lambda item: int(item[1]), reverse=True)
    rank = 4
    for idx, (player_id, _) in enumerate(ordered, start=1):
        if player_id == agent_id:
            rank = idx
            break

    decision_count = 0
    fallback_count = 0
    try:
        agent_obj = game_director.game_manager.agent_manager.players[position]["player"]
        if hasattr(agent_obj, "get_llm_decision_history"):
            history = agent_obj.get_llm_decision_history()
            decision_count = len(history)
            fallback_count = sum(1 for item in history if item.get("fallback"))
    except Exception:
        pass

    return victory, points, rank, decision_count, fallback_count


def simulate_match(
    opponents: Sequence[type],
    position: int,
    student_agent_class: type,
    params: Optional[Any],
    max_rounds: int,
    match_seed: int,
):
    try:
        random.seed(match_seed)
        configured_student = build_agent_class(student_agent_class, params)

        match_agents = list(opponents)
        match_agents.insert(position, configured_student)

        game_director = GameDirector(
            agents=match_agents,
            max_rounds=max_rounds,
            store_trace=False,
        )
        return extract_match_outcome(game_director, position)
    except Exception as exc:
        print("Exception:", repr(exc))
        print(traceback.format_exc())
        return (0, 0, 4, 0, 0)


def initialize_results(agent_specs: Sequence[Tuple[str, Optional[Any]]], seeds: Sequence[int]):
    results: Dict[Tuple[str, int], Dict[str, float]] = {}
    for agent_path, params in agent_specs:
        identifier = agent_identifier(agent_path, params)
        for seed in seeds:
            results[(identifier, seed)] = {
                "wins": 0,
                "points": 0,
                "rank_sum": 0,
                "decisions": 0,
                "fallback_count": 0,
                "matches": 0,
            }
    return results


def _finalize_summary_rows(
    benchmark_type: str,
    agent_specs: Sequence[Tuple[str, Optional[Any]]],
    seeds: Sequence[int],
    results: Dict[Tuple[str, int], Dict[str, float]],
) -> List[Dict[str, Any]]:
    llm_provider = os.getenv("CATAN_LLM_PROVIDER", "")
    llm_model = os.getenv("CATAN_LLM_MODEL", "")
    summary_rows: List[Dict[str, Any]] = []

    for agent_path, params in agent_specs:
        agent_name = safe_agent_name(agent_path)
        identifier = agent_identifier(agent_path, params)
        for seed in seeds:
            stats = results[(identifier, seed)]
            matches = int(stats["matches"])
            wins = int(stats["wins"])
            points = int(stats["points"])
            rank_sum = float(stats["rank_sum"])
            decisions = int(stats["decisions"])
            fallback_count = int(stats["fallback_count"])

            winrate = (wins / matches) if matches else 0.0
            avg_points = (points / matches) if matches else 0.0
            avg_rank = (rank_sum / matches) if matches else 0.0
            fallback_rate = (fallback_count / decisions) if decisions else 0.0

            summary_rows.append(
                {
                    "agent_path": agent_path,
                    "agent_name": agent_name,
                    "benchmark_type": benchmark_type,
                    "seed": seed,
                    "matches": matches,
                    "wins": wins,
                    "winrate": f"{winrate:.4f}",
                    "points_total": points,
                    "avg_points": f"{avg_points:.4f}",
                    "avg_rank": f"{avg_rank:.4f}",
                    "llm_decisions": decisions,
                    "fallback_count": fallback_count,
                    "fallback_rate": f"{fallback_rate:.4f}",
                    "provider": llm_provider if decisions > 0 else "",
                    "model": llm_model if decisions > 0 else "",
                }
            )

    summary_rows.sort(key=lambda row: (row["agent_name"], int(row["seed"])))
    return summary_rows


def write_summary_csv(output_path: Path, rows: Sequence[Dict[str, Any]]) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open(mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=BENCHMARK_SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def valid_standard_agent_classes() -> List[type]:
    classes = [load_agent_class(path) for path in STANDARD_AGENT_PATHS]
    return [
        agent_class
        for agent_class in classes
        if inspect.isclass(agent_class) and issubclass(agent_class, AgIn)
    ]


def run_benchmark_vs_random(
    output_filename: str = "benchmark_vs_random_resultados.csv",
) -> Tuple[List[Dict[str, Any]], Path]:
    load_repo_env_file()

    seeds = parse_seeds()
    n_matches = int(os.getenv("CATAN_BENCH_N_MATCHES", "25"))
    max_rounds = int(os.getenv("CATAN_BENCH_MAX_ROUNDS", "200"))
    workers = parse_worker_count()

    agent_specs = parse_agent_specs()
    agent_classes = {
        agent_identifier(path, params): (path, params, load_agent_class(path))
        for path, params in agent_specs
    }
    random_agent_class = load_agent_class("PyCatan.Agents.RandomAgent.RandomAgent")

    print(f"Seeds: {seeds}")
    print(f"Agentes a evaluar: {len(agent_specs)}")
    print(f"Workers: {workers}")

    results = initialize_results(agent_specs, seeds)

    tasks = []
    for seed in seeds:
        for agent_path, params in agent_specs:
            identifier = agent_identifier(agent_path, params)
            _, _, agent_class = agent_classes[identifier]
            for position in range(4):
                for match_idx in range(n_matches):
                    match_seed = stable_match_seed("random", seed, identifier, position, match_idx)
                    tasks.append(
                        (
                            [random_agent_class, random_agent_class, random_agent_class],
                            position,
                            agent_class,
                            params,
                            max_rounds,
                            match_seed,
                            identifier,
                            seed,
                        )
                    )

    print(f"Total de partidas a simular (vs random): {len(tasks)}")
    completed = 0

    with create_parallel_executor(max_workers=workers) as executor:
        future_map = {
            executor.submit(
                simulate_match,
                opponents,
                position,
                agent_class,
                params,
                max_rounds_task,
                match_seed,
            ): (identifier, seed)
            for (
                opponents,
                position,
                agent_class,
                params,
                max_rounds_task,
                match_seed,
                identifier,
                seed,
            ) in tasks
        }

        for future in concurrent.futures.as_completed(future_map):
            identifier, seed = future_map[future]
            victory, points, rank, decisions, fallback_count = future.result()
            stats = results[(identifier, seed)]
            stats["wins"] += victory
            stats["points"] += points
            stats["rank_sum"] += rank
            stats["decisions"] += decisions
            stats["fallback_count"] += fallback_count
            stats["matches"] += 1
            completed += 1
            if completed % 200 == 0 or completed == len(tasks):
                print(f"Progreso vs random: {completed}/{len(tasks)} ({completed/len(tasks):.2%})")

    rows = _finalize_summary_rows("vs_random", agent_specs, seeds, results)
    output_path = Path(__file__).resolve().parent / output_filename
    write_summary_csv(output_path, rows)
    return rows, output_path


def _iter_standard_tasks(
    agent_specs: Sequence[Tuple[str, Optional[Any]]],
    seeds: Sequence[int],
    n_matches_per_permutation: int,
    max_permutations: int,
    max_rounds: int,
) -> Iterable[Tuple[List[type], int, type, Optional[Any], int, int, str, int]]:
    benchmark_agents = valid_standard_agent_classes()
    all_permutations = list(itertools.permutations(benchmark_agents, 3))

    agent_classes = {
        agent_identifier(path, params): (path, params, load_agent_class(path))
        for path, params in agent_specs
    }

    for seed in seeds:
        rng = random.Random(seed)
        permutations = list(all_permutations)
        if max_permutations > 0 and len(permutations) > max_permutations:
            permutations = rng.sample(permutations, max_permutations)

        for agent_path, params in agent_specs:
            identifier = agent_identifier(agent_path, params)
            _, _, agent_class = agent_classes[identifier]
            for perm_idx, permutation in enumerate(permutations):
                opponents = list(permutation)
                for position in range(4):
                    for match_idx in range(n_matches_per_permutation):
                        match_seed = stable_match_seed(
                            "standard",
                            seed,
                            identifier,
                            perm_idx,
                            position,
                            match_idx,
                        )
                        yield (
                            opponents,
                            position,
                            agent_class,
                            params,
                            max_rounds,
                            match_seed,
                            identifier,
                            seed,
                        )


def run_benchmark_vs_standard(
    output_filename: str = "benchmark_vs_estandar_resultados.csv",
) -> Tuple[List[Dict[str, Any]], Path]:
    load_repo_env_file()

    seeds = parse_seeds()
    n_matches_per_permutation = int(os.getenv("CATAN_BENCH_N_MATCHES_PER_PERM", "5"))
    max_permutations = int(os.getenv("CATAN_BENCH_MAX_PERMUTATIONS", "25"))
    max_rounds = int(os.getenv("CATAN_BENCH_MAX_ROUNDS", "200"))
    workers = parse_worker_count()

    agent_specs = parse_agent_specs()
    results = initialize_results(agent_specs, seeds)

    tasks = list(
        _iter_standard_tasks(
            agent_specs=agent_specs,
            seeds=seeds,
            n_matches_per_permutation=n_matches_per_permutation,
            max_permutations=max_permutations,
            max_rounds=max_rounds,
        )
    )

    print(f"Seeds: {seeds}")
    print(f"Agentes a evaluar: {len(agent_specs)}")
    print(f"Workers: {workers}")
    print(f"Total de partidas a simular (vs estándar): {len(tasks)}")

    completed = 0
    with create_parallel_executor(max_workers=workers) as executor:
        future_map = {
            executor.submit(
                simulate_match,
                opponents,
                position,
                agent_class,
                params,
                max_rounds_task,
                match_seed,
            ): (identifier, seed)
            for (
                opponents,
                position,
                agent_class,
                params,
                max_rounds_task,
                match_seed,
                identifier,
                seed,
            ) in tasks
        }

        for future in concurrent.futures.as_completed(future_map):
            identifier, seed = future_map[future]
            victory, points, rank, decisions, fallback_count = future.result()
            stats = results[(identifier, seed)]
            stats["wins"] += victory
            stats["points"] += points
            stats["rank_sum"] += rank
            stats["decisions"] += decisions
            stats["fallback_count"] += fallback_count
            stats["matches"] += 1
            completed += 1
            if completed % 1000 == 0 or completed == len(tasks):
                print(
                    f"Progreso vs estándar: {completed}/{len(tasks)} ({completed/len(tasks):.2%})"
                )

    rows = _finalize_summary_rows("vs_standard", agent_specs, seeds, results)
    output_path = Path(__file__).resolve().parent / output_filename
    write_summary_csv(output_path, rows)
    return rows, output_path
