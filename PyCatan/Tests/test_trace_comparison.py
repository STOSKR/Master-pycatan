import json
import random
import unittest
from pathlib import Path

from PyCatan.Agents.AdrianHerasAgent import AdrianHerasAgent as aha
from PyCatan.Agents.RandomAgent import RandomAgent as ra
from PyCatan.Managers.GameDirector import GameDirector


class TestTraceComparison(unittest.TestCase):
    def test_reference_traces_are_stable(self):
        trace_dir = Path(__file__).resolve().parent / "test_traces"
        game_director = GameDirector(agents=(ra, ra, aha, aha), max_rounds=200)

        for i in range(100):
            with self.subTest(game=i):
                random.seed(i)
                game_trace = game_director.game_start(i, False)
                generated_hash = hash(json.dumps(game_trace))

                reference_path = trace_dir / f"game_{i}.json"
                reference_hash = hash(reference_path.read_text(encoding="utf-8"))

                self.assertEqual(generated_hash, reference_hash)
