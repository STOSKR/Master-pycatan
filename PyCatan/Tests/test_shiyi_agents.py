import unittest

from PyCatan.Agents.RandomAgent import RandomAgent
from PyCatan.Agents.ShiyiHeuristicAgent import ShiyiHeuristicAgent
from PyCatan.Agents.ShiyiLLMAgent import ShiyiLLMAgent
from PyCatan.Agents.llm_engine import BaseLLMProvider, LLMGeneration
from PyCatan.Classes.Board import Board
from PyCatan.Managers.GameDirector import GameDirector


class StaticProvider(BaseLLMProvider):
    provider_name = "static"

    def __init__(self, model: str, action_index: int):
        self.model = model
        self.action_index = action_index

    def generate(self, system_prompt: str, user_prompt: str, timeout_seconds: float) -> LLMGeneration:
        return LLMGeneration(text='{"action_index": %d}' % self.action_index, raw_response={})


class TestShiyiAgents(unittest.TestCase):
    def test_shiyi_heuristic_game_start_legal(self):
        board = Board()
        agent = ShiyiHeuristicAgent(agent_id=0)
        node_id, road_to = agent.on_game_start(board)
        self.assertIn(node_id, board.valid_starting_nodes())
        self.assertIn(road_to, board.nodes[node_id]["adjacent"])

    def test_shiyi_llm_game_start_legal(self):
        board = Board()
        agent = ShiyiLLMAgent(agent_id=0, provider=StaticProvider("stub", 0))
        node_id, road_to = agent.on_game_start(board)
        self.assertIn(node_id, board.valid_starting_nodes())
        self.assertIn(road_to, board.nodes[node_id]["adjacent"])

    def test_shiyi_heuristic_smoke_game(self):
        game_director = GameDirector(
            agents=[ShiyiHeuristicAgent, RandomAgent, RandomAgent, RandomAgent],
            max_rounds=30,
            store_trace=False,
        )
        trace = game_director.game_start(print_outcome=False)
        self.assertIn("game", trace)


if __name__ == "__main__":
    unittest.main()
