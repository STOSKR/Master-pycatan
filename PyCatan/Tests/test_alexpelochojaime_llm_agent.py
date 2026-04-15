import unittest

from PyCatan.Agents.AlexPelochoJaimeLLMAgent import AlexPelochoJaimeLLMAgent
from PyCatan.Agents.llm_engine import BaseLLMProvider, LLMGeneration
from PyCatan.Classes.Board import Board


class StaticProvider(BaseLLMProvider):
    provider_name = "static"

    def __init__(self, model: str, action_index: int):
        self.model = model
        self.action_index = action_index

    def generate(self, system_prompt: str, user_prompt: str, timeout_seconds: float) -> LLMGeneration:
        return LLMGeneration(text='{"action_index": %d}' % self.action_index, raw_response={})


class TestAlexPelochoJaimeLLMAgent(unittest.TestCase):
    def test_on_game_start_returns_legal_choice_with_llm(self):
        board = Board()
        agent = AlexPelochoJaimeLLMAgent(agent_id=0, provider=StaticProvider("stub", 0))

        node_id, road_to = agent.on_game_start(board)

        self.assertIn(node_id, board.valid_starting_nodes())
        self.assertIn(road_to, board.nodes[node_id]["adjacent"])
        self.assertTrue(agent.get_llm_decision_history())

    def test_on_build_phase_handles_end_action(self):
        board = Board()
        agent = AlexPelochoJaimeLLMAgent(agent_id=0, provider=StaticProvider("stub", 0))

        action = agent.on_build_phase(board)

        self.assertIsNone(action)


if __name__ == "__main__":
    unittest.main()
