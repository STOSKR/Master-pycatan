import os
import importlib
from Agents.RandomAgent import RandomAgent as ra
from Managers.GameDirector import GameDirector

def cargar_agente(ruta_clase):
    modulo, clase = ruta_clase.rsplit(".", 1)
    mod = importlib.import_module(modulo)
    return getattr(mod, clase)

def run_test():
    agente_alumno_clase_path = "Agents.AlexPelochoJaimeLLMAgent.AlexPelochoJaimeLLMAgent"
    agente_alumno_clase = cargar_agente(agente_alumno_clase_path)
    position = 2
    max_rounds = 30

    # Match setup similar to GameDirector.run_match logic (inferred)
    # Based on benchmark_vs_random.py logic, we create GameDirector and start match
    
    # We need to see how GameDirector is initialized. 
    # Usually it takes agents or similar. 
    # In benchmark_vs_random: director = GameDirector(agentes, max_rounds=max_rounds)
    
    agentes_match = [ra, ra, ra, ra]
    agentes_match[position] = agente_alumno_clase
    
    director = GameDirector(agentes_match, max_rounds=max_rounds)
    director.run_game()
    
    print("--- Players Info ---")
    players = director.game_manager.agent_manager.players
    for i, p in enumerate(players):
        print(f"Index {i}: ID={p.id}, Class={p.__class__.__name__}")
        if p.__class__.__name__ == "AlexPelochoJaimeLLMAgent":
            print(f"MATCH FOUND: AlexPelochoJaimeLLMAgent is at index {i}")

    print("--- Decision History Lengths ---")
    for i, p in enumerate(players):
        if hasattr(p, 'get_llm_decision_history'):
            history = p.get_llm_decision_history()
            print(f"Player {i} history length: {len(history)}")
        elif hasattr(p, 'llm_decision_history'):
             print(f"Player {i} history length (direct attr): {len(p.llm_decision_history)}")

if __name__ == "__main__":
    run_test()
