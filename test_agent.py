import os
import sys
from collections import Counter
try:
    from PyCatan.Managers.GameDirector import GameDirector
    from PyCatan.Agents.RandomAgent import RandomAgent
    from PyCatan.Agents.AlexPelochoJaimeLLMAgent import AlexPelochoJaimeLLMAgent, LLMBehaviorConfig
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

os.environ['CATAN_LLM_PROVIDER']='ollama'
os.environ['CATAN_LLM_MODEL']='qwen2.5:0.5b'

class FastLLMAgent(AlexPelochoJaimeLLMAgent):
    def __init__(self, agent_id):
        super().__init__(
            agent_id,
            llm_config=LLMBehaviorConfig(
                enable_on_game_start=True,
                enable_on_build_phase=True,
                max_actions_on_game_start=8,
                max_actions_on_build_phase=8,
                decision_timeout_seconds=2.0,
            ),
        )

agents=[FastLLMAgent, RandomAgent, RandomAgent, RandomAgent]
gd=GameDirector(agents=agents, max_rounds=12, store_trace=False)
gd.game_start(print_outcome=False)
player=gd.game_manager.agent_manager.players[0]['player']
h=player.get_llm_decision_history()
rc=Counter(x.get('reason','unknown') for x in h)
fc=sum(1 for x in h if x.get('fallback'))
print(f'decisions {len(h)}')
print(f'fallbacks {fc}')
print(f'fallback_rate {(fc/len(h) if h else 0.0)}')
print(f'reasons {rc.most_common(10)}')
