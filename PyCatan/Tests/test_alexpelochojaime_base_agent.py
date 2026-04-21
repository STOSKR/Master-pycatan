import unittest
from unittest.mock import patch

from PyCatan.Agents.ShiyiBaseAgent import (
    ShiyiBaseAgent,
    IncrementalFeatureFlags,
)
from PyCatan.Agents.RandomAgent import RandomAgent
from PyCatan.Classes.Board import Board


class TestAlexPelochoJaimeBaseAgent(unittest.TestCase):
    def test_on_game_start_delegates_to_random_when_flag_disabled(self):
        board = Board()
        agent = ShiyiBaseAgent(
            agent_id=0,
            feature_flags=IncrementalFeatureFlags.random_baseline(),
        )

        with patch.object(RandomAgent, "on_game_start", return_value=(7, 8)) as mock_random:
            response = agent.on_game_start(board)

        self.assertEqual(response, (7, 8))
        mock_random.assert_called_once()

    def test_on_game_start_falls_back_to_random_on_error(self):
        board = Board()
        agent = ShiyiBaseAgent(agent_id=0)

        with patch(
            "PyCatan.Agents.ShiyiBaseAgent.choose_best_node",
            side_effect=RuntimeError("boom"),
        ):
            with patch.object(RandomAgent, "on_game_start", return_value=(4, 5)):
                response = agent.on_game_start(board)

        self.assertEqual(response, (4, 5))

    def test_on_build_phase_delegates_to_random_when_flag_disabled(self):
        board = Board()
        agent = ShiyiBaseAgent(
            agent_id=0,
            feature_flags={"on_build_phase": False},
        )

        sentinel = {"building": "road", "node_id": 0, "road_to": 1}
        with patch.object(RandomAgent, "on_build_phase", return_value=sentinel) as mock_random:
            response = agent.on_build_phase(board)

        self.assertEqual(response, sentinel)
        mock_random.assert_called_once()


if __name__ == "__main__":
    unittest.main()
