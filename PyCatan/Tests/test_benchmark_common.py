import os
import unittest
from unittest.mock import patch

from PyCatan.benchmark_common import parse_agent_specs, parse_seeds, stable_match_seed


class TestBenchmarkCommon(unittest.TestCase):
    def test_parse_seeds_default(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(parse_seeds(), [42, 31415, 2026])

    def test_parse_agent_specs_from_json(self):
        with patch.dict(
            os.environ,
            {
                "CATAN_BENCH_AGENTS": (
                    '[{"class":"PyCatan.Agents.RandomAgent.RandomAgent","params":null}]'
                )
            },
            clear=True,
        ):
            specs = parse_agent_specs()

        self.assertEqual(specs, [("PyCatan.Agents.RandomAgent.RandomAgent", None)])

    def test_stable_match_seed_is_deterministic(self):
        seed_a = stable_match_seed("random", 42, "agent_path", 0, 0)
        seed_b = stable_match_seed("random", 42, "agent_path", 0, 0)
        seed_c = stable_match_seed("random", 42, "agent_path", 0, 1)

        self.assertEqual(seed_a, seed_b)
        self.assertNotEqual(seed_a, seed_c)


if __name__ == "__main__":
    unittest.main()
