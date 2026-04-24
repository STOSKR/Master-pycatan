import unittest

from PyCatan.Agents.RandomAgent import RandomAgent
from PyCatan.Agents.ShiyiHeuristicAgent import ShiyiHeuristicAgent
from PyCatan.Agents.ShiyiLLMAgent import ShiyiLLMAgent
from PyCatan.Agents.llm_engine import BaseLLMProvider, LLMGeneration
from PyCatan.Classes.Board import Board
from PyCatan.Classes.Constants import BuildConstants
from PyCatan.Classes.Materials import Materials
from PyCatan.Managers.GameDirector import GameDirector


class StaticProvider(BaseLLMProvider):
    provider_name = "static"

    def __init__(self, model: str, action_index: int):
        self.model = model
        self.action_index = action_index

    def generate(self, system_prompt: str, user_prompt: str, timeout_seconds: float) -> LLMGeneration:
        return LLMGeneration(text='{"action_index": %d}' % self.action_index, raw_response={})


class InvalidProvider(BaseLLMProvider):
    provider_name = "invalid"

    def __init__(self, model: str):
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str, timeout_seconds: float) -> LLMGeneration:
        return LLMGeneration(text="not-json", raw_response={})


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

    def test_shiyi_heuristic_build_phase_buys_card_when_only_card_is_affordable(self):
        board = Board()
        agent = ShiyiHeuristicAgent(agent_id=0)
        agent.hand.resources = Materials(1, 1, 0, 0, 1)

        action = agent.on_build_phase(board)

        self.assertEqual(action, {"building": BuildConstants.CARD})

    def test_shiyi_heuristic_commerce_phase_proposes_bank_trade(self):
        agent = ShiyiHeuristicAgent(agent_id=0)
        agent.board = Board()
        agent.hand.resources = Materials(6, 0, 0, 0, 0)

        trade = agent.on_commerce_phase()

        self.assertIsNotNone(trade)
        self.assertEqual(trade["gives"], 0)
        self.assertIn(trade["receives"], [0, 1, 2, 3, 4])

    def test_shiyi_llm_build_phase_invalid_response_falls_back_to_heuristic(self):
        board = Board()
        agent = ShiyiLLMAgent(agent_id=0, provider=InvalidProvider("stub"))
        agent.hand.resources = Materials(1, 1, 0, 0, 1)

        action = agent.on_build_phase(board)
        history = agent.get_llm_decision_history()

        self.assertEqual(action, {"building": BuildConstants.CARD})
        self.assertEqual(len(history), 1)
        self.assertTrue(history[0]["fallback"])


if __name__ == "__main__":
    unittest.main()
