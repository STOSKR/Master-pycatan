import os
import time
import concurrent.futures
import importlib
import itertools
import random
import inspect
import csv
import traceback

from Agents.RandomAgent import RandomAgent as ra
from Agents.AdrianHerasAgent import AdrianHerasAgent as aha
from Agents.AlexPastorAgent import AlexPastorAgent as apa
from Agents.AlexPelochoJaimeAgent import AlexPelochoJaimeAgent as apja
from Agents.CarlesZaidaAgent import CarlesZaidaAgent as cza
from Agents.CrabisaAgent import CrabisaAgent as ca
from Agents.EdoAgent import EdoAgent as ea
from Agents.PabloAleixAlexAgent import PabloAleixAlexAgent as paaa
from Agents.SigmaAgent import SigmaAgent as sa
from Agents.TristanAgent import TristanAgent as ta
from Managers.GameDirector import GameDirector
from PyCatan.Interfaces.AgentInterface import AgentInterface as AgIn

BENCHMARK_AGENTS = [ra, aha, apa, apja, cza, ca, ea, paaa, sa, ta]

n_matches_per_permutation = int(os.getenv("CATAN_BENCH_N_MATCHES_PER_PERM", "5"))
max_permutations = int(os.getenv("CATAN_BENCH_MAX_PERMUTATIONS", "25"))
random_seed = int(os.getenv("CATAN_BENCH_RANDOM_SEED", "42"))
porcentaje_workers = float(os.getenv("CATAN_BENCH_WORKERS_PCT", "0.95"))
max_rounds = int(os.getenv("CATAN_BENCH_MAX_ROUNDS", "200"))

# Agentes a evaluar: (ruta_clase, params)
agentes_a_evaluar = [
    ("Agents.AlexPelochoJaimeHeuristicAgent.AlexPelochoJaimeHeuristicAgent", None),
    ("Agents.AlexPelochoJaimeLLMAgent.AlexPelochoJaimeLLMAgent", None),
    # Se pueden poner varios agentes para evaluar y comparar, con y sin parámetros personalizados, por si queremos probar varias configuraciones del mismo agente.
]


def cargar_agente(ruta_clase):
    modulo, clase = ruta_clase.rsplit(".", 1)
    mod = importlib.import_module(modulo)
    return getattr(mod, clase)


def crear_clase_agente_configurada(agente_clase, **kwargs):
    class AgenteConfigurado(agente_clase):
        def __init__(self, agent_id):
            super().__init__(agent_id, **kwargs)

    AgenteConfigurado.__name__ = f"{agente_clase.__name__}_ConfiguradoDict"
    return AgenteConfigurado


def crear_clase_agente_configurada_lista(agente_clase, params_list):
    class AgenteConfigurado(agente_clase):
        def __init__(self, agent_id):
            super().__init__(agent_id, *params_list)

    AgenteConfigurado.__name__ = f"{agente_clase.__name__}_ConfiguradoLista"
    return AgenteConfigurado


def simulate_match(opponents, position, agente_alumno_clase, params=None):
    try:
        if params is not None:
            if isinstance(params, (list, tuple)):
                agente_alumno_class = crear_clase_agente_configurada_lista(
                    agente_alumno_clase, params
                )
            elif isinstance(params, dict):
                agente_alumno_class = crear_clase_agente_configurada(
                    agente_alumno_clase, **params
                )
            else:
                raise TypeError("params debe ser lista/tupla o dict")
        else:
            agente_alumno_class = agente_alumno_clase

        match_agents = list(opponents)
        match_agents.insert(position, agente_alumno_class)

        game_director = GameDirector(
            agents=match_agents, max_rounds=max_rounds, store_trace=False
        )
        game_trace = game_director.game_start(print_outcome=False)

        last_round = max(game_trace["game"].keys(), key=lambda r: int(r.split("_")[-1]))
        last_turn = max(
            game_trace["game"][last_round].keys(),
            key=lambda t: int(t.split("_")[-1].lstrip("P")),
        )
        victory_points = game_trace["game"][last_round][last_turn]["end_turn"][
            "victory_points"
        ]

        agent_id = f"J{position}"
        points = int(victory_points[agent_id])
        winner = max(victory_points, key=lambda player: int(victory_points[player]))
        victory = 1 if winner == agent_id else 0

        ordenados = sorted(
            victory_points.items(), key=lambda item: int(item[1]), reverse=True
        )
        rank = 4  # Default rank if agent not found
        for idx, (jugador, _) in enumerate(ordenados, start=1):
            if jugador == agent_id:
                rank = idx
                break

        decision_count = 0
        fallback_count = 0
        try:
            agent_obj = game_director.game_manager.agent_manager.players[position][
                "player"
            ]
            if hasattr(agent_obj, "get_llm_decision_history"):
                decision_history = agent_obj.get_llm_decision_history()
                decision_count = len(decision_history)
                fallback_count = sum(
                    1 for decision in decision_history if decision.get("fallback")
                )
        except Exception:
            # Keep benchmark resilient even if internal history structure changes.
            pass

        return (victory, points, rank, decision_count, fallback_count)
    except Exception as e:
        print("Exception:", repr(e))
        print(traceback.format_exc())
        return (0, 0, 4, 0, 0)


if __name__ == "__main__":
    llm_provider = os.getenv("CATAN_LLM_PROVIDER", "")
    llm_model = os.getenv("CATAN_LLM_MODEL", "")

    results = {
        agent + str(params) if params is not None else agent: {
            "wins": 0,
            "points": 0,
            "rank_sum": 0,
            "decisions": 0,
            "fallback_count": 0,
        }
        for agent, params in agentes_a_evaluar
    }

    total_workers = os.cpu_count() or 1
    workers_a_utilizar = max(1, int(total_workers * porcentaje_workers))
    print(f"Workers a utilizar ({porcentaje_workers*100}%): {workers_a_utilizar}")

    start_time = time.time()

    benchmark_agents_validos = [
        agent
        for agent in BENCHMARK_AGENTS
        if inspect.isclass(agent) and issubclass(agent, AgIn)
    ]
    print(
        f"Agentes benchmark válidos: {len(benchmark_agents_validos)} de {len(BENCHMARK_AGENTS)}"
    )

    permutations = list(itertools.permutations(benchmark_agents_validos, 3))
    if max_permutations > 0 and len(permutations) > max_permutations:
        random.seed(random_seed)
        permutations = random.sample(permutations, max_permutations)
    total_matches = (
        len(agentes_a_evaluar) * len(permutations) * 4 * n_matches_per_permutation
    )
    coste_medio_partida_segundos = 0.004
    print(
        f"Total de partidas a simular: {total_matches}. Tiempo estimado: {total_matches * coste_medio_partida_segundos / 60:.2f} minutos"
    )

    matches_done = 0
    batch_size = 10000
    futures_batch = []
    resumen_csv = []
    csv_fieldnames = [
        "Agente",
        "Tipo Agente",
        "Partidas",
        "Victorias",
        "Ratio Victorias",
        "Puntos Totales",
        "Media Puntos",
        "Puesto Medio",
        "Decisiones LLM",
        "Fallback Count",
        "Fallback Rate",
        "LLM Provider",
        "LLM Model",
    ]

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=workers_a_utilizar
    ) as executor:

        def task_generator():
            for agente_path, params in agentes_a_evaluar:
                agente_cls = cargar_agente(agente_path)
                for perm in permutations:
                    for pos in range(4):
                        for _ in range(n_matches_per_permutation):
                            yield (list(perm), pos, agente_cls, params, agente_path)

        for perm, pos, agente_cls, params, agente_path in task_generator():
            fut = executor.submit(simulate_match, perm, pos, agente_cls, params=params)
            futures_batch.append(
                (fut, agente_path + str(params) if params is not None else agente_path)
            )

            if len(futures_batch) >= batch_size:
                futures_dict = {
                    fut: agente_alumno for fut, agente_alumno in futures_batch
                }
                for fut in concurrent.futures.as_completed(futures_dict):
                    victory, points, rank, decisions, fallback_count = fut.result()
                    agent = futures_dict[fut]
                    results[agent]["wins"] += victory
                    results[agent]["points"] += points
                    results[agent]["rank_sum"] += rank
                    results[agent]["decisions"] += decisions
                    results[agent]["fallback_count"] += fallback_count
                    matches_done += 1
                    if matches_done % 10000 == 0 or matches_done == total_matches:
                        print(
                            f"Progreso: {matches_done}/{total_matches} partidas completadas ({matches_done/total_matches:.2%})"
                        )
                futures_batch = []

        if futures_batch:
            futures_dict = {fut: agente_alumno for fut, agente_alumno in futures_batch}
            for fut in concurrent.futures.as_completed(futures_dict):
                victory, points, rank, decisions, fallback_count = fut.result()
                agent = futures_dict[fut]
                results[agent]["wins"] += victory
                results[agent]["points"] += points
                results[agent]["rank_sum"] += rank
                results[agent]["decisions"] += decisions
                results[agent]["fallback_count"] += fallback_count
                matches_done += 1
                if matches_done % 10000 == 0 or matches_done == total_matches:
                    print(
                        f"Progreso: {matches_done}/{total_matches} partidas completadas ({matches_done/total_matches:.2%})"
                    )

    partidas_por_agente = len(permutations) * 4 * n_matches_per_permutation
    print("\nResultados ordenados por ratio de victorias:")

    resumen = []
    for agente, stats in results.items():
        nombre = agente
        wins = stats["wins"]
        points = stats["points"]
        rank_sum = stats["rank_sum"]
        decisions = stats["decisions"]
        fallback_count = stats["fallback_count"]
        ratio = wins / partidas_por_agente
        avg_points = points / partidas_por_agente
        puesto_medio = rank_sum / partidas_por_agente
        fallback_rate = (fallback_count / decisions) if decisions else 0.0
        resumen.append(
            (
                nombre,
                wins,
                points,
                partidas_por_agente,
                ratio,
                avg_points,
                puesto_medio,
                decisions,
                fallback_count,
                fallback_rate,
            )
        )

    resumen.sort(key=lambda x: x[4], reverse=True)

    for (
        nombre,
        wins,
        points,
        total,
        ratio,
        avg_points,
        puesto_medio,
        decisions,
        fallback_count,
        fallback_rate,
    ) in resumen:
        print(
            f"{nombre}: {wins} victorias, {points} puntos en {total} partidas — "
            f"Ratio: {ratio:.2%}, Media puntos: {avg_points:.2f}, Puesto medio: {puesto_medio:.2f}, "
            f"Fallback rate: {fallback_rate:.2%} ({fallback_count}/{decisions})"
        )
        tipo_agente = "LLM" if "LLM" in nombre else "Heuristico"
        resumen_csv.append(
            {
                "Agente": nombre,
                "Tipo Agente": tipo_agente,
                "Partidas": total,
                "Victorias": wins,
                "Ratio Victorias": f"{ratio:.4f}",
                "Puntos Totales": points,
                "Media Puntos": f"{avg_points:.2f}",
                "Puesto Medio": f"{puesto_medio:.2f}",
                "Decisiones LLM": decisions,
                "Fallback Count": fallback_count,
                "Fallback Rate": f"{fallback_rate:.4f}",
                "LLM Provider": llm_provider if tipo_agente == "LLM" else "",
                "LLM Model": llm_model if tipo_agente == "LLM" else "",
            }
        )

    # Guardar CSV
    csv_filename = "benchmark_vs_estandar_resultados.csv"
    with open(csv_filename, mode="w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_fieldnames)
        writer.writeheader()
        writer.writerows(resumen_csv)

    print(f"\n Resultados guardados en: {csv_filename}")

    end_time = time.time()
    horas, resto = divmod(end_time - start_time, 3600)
    minutos, segundos = divmod(resto, 60)
    print(f"\n Tiempo total: {int(horas)}h {int(minutos)}m {int(segundos)}s")
