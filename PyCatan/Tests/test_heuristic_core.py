import unittest

from PyCatan.Agents.heuristic_core import (
    HeuristicWeights,
    choose_bank_trade,
    choose_best_node,
    choose_best_starting_road,
    choose_material_for_monopoly,
)
from PyCatan.Classes.Board import Board
from PyCatan.Classes.Constants import BuildConstants
from PyCatan.Classes.Materials import Materials


class TestHeuristicCore(unittest.TestCase):
    def setUp(self):
        self.board = Board()
        self.weights = HeuristicWeights()

    def test_best_starting_node_is_valid(self):
        valid_nodes = self.board.valid_starting_nodes()
        best = choose_best_node(self.board, valid_nodes, self.weights)
        self.assertIn(best, valid_nodes)

    def test_best_starting_road_is_adjacent(self):
        valid_nodes = self.board.valid_starting_nodes()
        best = choose_best_node(self.board, valid_nodes, self.weights)
        road_to = choose_best_starting_road(self.board, best, self.weights)
        self.assertIn(road_to, self.board.nodes[best]["adjacent"])

    def test_bank_trade_suggests_needed_resource(self):
        resources = Materials(6, 0, 0, 0, 0)
        trade = choose_bank_trade(
            board=self.board,
            player_id=0,
            resources=resources,
            target_building=BuildConstants.CITY,
        )

        self.assertIsNotNone(trade)
        self.assertEqual(trade["gives"], 0)
        self.assertIn(trade["receives"], (0, 1))

    def test_monopoly_choice_is_valid_material_id(self):
        resources = Materials(0, 0, 0, 0, 0)
        material = choose_material_for_monopoly(resources)
        self.assertIn(material, [0, 1, 2, 3, 4])


if __name__ == "__main__":
    unittest.main()
