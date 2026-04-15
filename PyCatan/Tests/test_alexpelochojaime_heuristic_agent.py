import unittest

from PyCatan.Agents.AlexPelochoJaimeHeuristicAgent import AlexPelochoJaimeHeuristicAgent
from PyCatan.Agents.RandomAgent import RandomAgent
from PyCatan.Classes.Board import Board
from PyCatan.Managers.GameDirector import GameDirector


class TestAlexPelochoJaimeHeuristicAgent(unittest.TestCase):
    def test_on_game_start_returns_legal_choice(self):
        board = Board()
        agent = AlexPelochoJaimeHeuristicAgent(agent_id=0)

        node_id, road_to = agent.on_game_start(board)

        self.assertIn(node_id, board.valid_starting_nodes())
        self.assertIn(road_to, board.nodes[node_id]["adjacent"])

    def test_smoke_game_runs_without_crashing(self):
        game_director = GameDirector(
            agents=[
                AlexPelochoJaimeHeuristicAgent,
                RandomAgent,
                RandomAgent,
                RandomAgent,
            ],
            max_rounds=60,
            store_trace=False,
        )

        trace = game_director.game_start(print_outcome=False)
        self.assertIn("game", trace)
        self.assertTrue(trace["game"])


if __name__ == "__main__":
    unittest.main()
