import os
import time
import importlib
import concurrent.futures
import csv
import traceback
from Agents.RandomAgent import RandomAgent as ra
from Managers.GameDirector import GameDirector

n_matches = int(os.getenv("CATAN_BENCH_N_MATCHES", "100"))
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


def simulate_match(position, agente_alumno_clase, params=None):
    try:
        if params is not None:
            if isinstance(params, (list, tuple)):
                agente_final = crear_clase_agente_configurada_lista(
                    agente_alumno_clase, params
                )
            elif isinstance(params, dict):
                agente_final = crear_clase_agente_configurada(
                    agente_alumno_clase, **params
                )
            else:
                raise TypeError("params debe ser lista/tupla o dict")
        else:
            agente_final = agente_alumno_clase

        match_agents = [ra, ra, ra]
        match_agents.insert(position, agente_final)

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
        rank = 4  # Default rank if player not found
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
        print("\n=== EXCEPCIÓN EN simulate_match ===")
        print(
            "Agente clase:",
            agente_alumno_clase,
            "name:",
            getattr(agente_alumno_clase, "__name__", None),
        )
        print("Posición:", position, "params type:", type(params), "params:", params)
        print("Exception:", repr(e))
        print(traceback.format_exc())
        return (0, 0, 4, 0, 0)


if __name__ == "__main__":
    llm_provider = os.getenv("CATAN_LLM_PROVIDER", "")
    llm_model = os.getenv("CATAN_LLM_MODEL", "")

    total_workers = os.cpu_count() or 1
    workers_a_utilizar = max(1, int(total_workers * porcentaje_workers))
    print(f"Workers a utilizar ({porcentaje_workers*100}%): {workers_a_utilizar}\n")

    start_time = time.time()
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

    for ruta_agente, params_agente in agentes_a_evaluar:
        agente_alumno = cargar_agente(ruta_agente)
        agent_name = agente_alumno.__name__
        print(f"\n==== Evaluando agente: {agent_name} ====\n")

        partial_start_time = time.time()
        position_results = {pos: 0 for pos in range(4)}
        total_wins = 0
        total_points = 0
        total_rank = 0
        total_decisions = 0
        total_fallback_count = 0

        with concurrent.futures.ProcessPoolExecutor(
            max_workers=workers_a_utilizar
        ) as executor:
            for pos in range(4):
                futures = [
                    executor.submit(simulate_match, pos, agente_alumno, params_agente)
                    for _ in range(n_matches)
                ]
                for f in concurrent.futures.as_completed(futures):
                    (
                        victory,
                        points,
                        rank,
                        decision_count,
                        fallback_count,
                    ) = f.result()
                    position_results[pos] += victory
                    total_wins += victory
                    total_points += points
                    total_rank += rank
                    total_decisions += decision_count
                    total_fallback_count += fallback_count

        for pos in range(4):
            wins = position_results[pos]
            percentage = 100 * wins / n_matches
            print(
                f"- Posición {pos+1}: {wins} victorias de {n_matches} partidas ({percentage:.2f}%)"
            )

        total_partidas = n_matches * 4
        ratio_victorias = total_wins / total_partidas
        media_puntos = total_points / total_partidas
        puesto_medio = total_rank / total_partidas
        fallback_rate = (
            total_fallback_count / total_decisions if total_decisions else 0.0
        )

        print(
            f"\nTotal para {agent_name}: {total_wins} victorias de {total_partidas} partidas ({ratio_victorias:.2%})"
        )
        print(f"Media de puntos: {media_puntos:.2f}")
        print(f"Puesto medio: {puesto_medio:.2f}")
        print(
            f"Fallback rate: {fallback_rate:.2%} ({total_fallback_count}/{total_decisions})"
        )

        tipo_agente = "LLM" if "LLM" in agent_name else "Heuristico"
        resumen_csv.append(
            {
                "Agente": agent_name,
                "Tipo Agente": tipo_agente,
                "Partidas": total_partidas,
                "Victorias": total_wins,
                "Ratio Victorias": f"{ratio_victorias:.4f}",
                "Puntos Totales": total_points,
                "Media Puntos": f"{media_puntos:.2f}",
                "Puesto Medio": f"{puesto_medio:.2f}",
                "Decisiones LLM": total_decisions,
                "Fallback Count": total_fallback_count,
                "Fallback Rate": f"{fallback_rate:.4f}",
                "LLM Provider": llm_provider if tipo_agente == "LLM" else "",
                "LLM Model": llm_model if tipo_agente == "LLM" else "",
            }
        )

        partial_end_time = time.time()
        horas, resto = divmod(partial_end_time - partial_start_time, 3600)
        minutos, segundos = divmod(resto, 60)
        print(f"Tiempo parcial: {int(horas)}h {int(minutos)}m {int(segundos)}s\n")

    # Guardar CSV
    csv_filename = "benchmark_vs_random_resultados.csv"
    with open(csv_filename, mode="w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_fieldnames)
        writer.writeheader()
        writer.writerows(resumen_csv)

    print(f"\nResultados guardados en: {csv_filename}")

    end_time = time.time()
    horas, resto = divmod(end_time - start_time, 3600)
    minutos, segundos = divmod(resto, 60)
    print(f"\nTiempo total: {int(horas)}h {int(minutos)}m {int(segundos)}s\n")
