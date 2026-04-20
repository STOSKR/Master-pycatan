import importlib
from collections import Counter

from PyCatan.Managers.GameDirector import GameDirector
from PyCatan.Agents.RandomAgent import RandomAgent

module = importlib.import_module("PyCatan.Agents.AlexPelochoJaimeLLMAgent")
LLMAgent = getattr(module, "AlexPelochoJaimeLLMAgent")

agents = [LLMAgent, RandomAgent, RandomAgent, RandomAgent]
game_director = GameDirector(agents=agents, max_rounds=40, store_trace=False)
game_director.game_start(print_outcome=False)

llm_player = game_director.game_manager.agent_manager.players[0]["player"]
history = llm_player.get_llm_decision_history()

reason_counts = Counter(item.get("reason", "unknown") for item in history)
fallback_count = sum(1 for item in history if item.get("fallback"))

print(f"decisions={len(history)}")
print(f"fallbacks={fallback_count}")
print(f"reason_counts={reason_counts.most_common(8)}")
