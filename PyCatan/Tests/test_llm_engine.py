import unittest

from PyCatan.Agents.llm_engine import (
    BaseLLMProvider,
    DecisionOutcome,
    LLMDecisionEngine,
    LLMGeneration,
)


class FakeProvider(BaseLLMProvider):
    provider_name = "fake"

    def __init__(self, model: str, response_text: str):
        self.model = model
        self._response_text = response_text

    def generate(self, system_prompt: str, user_prompt: str, timeout_seconds: float) -> LLMGeneration:
        return LLMGeneration(text=self._response_text, raw_response={})


class TestLLMDecisionEngine(unittest.TestCase):
    def test_provider_not_configured_uses_fallback(self):
        engine = LLMDecisionEngine(provider=None)
        actions = [{"a": 1}, {"a": 2}]

        outcome = engine.decide_action(
            decision_name="x",
            state={},
            legal_actions=actions,
            prompt_variant="compact_json",
            fallback_index=1,
        )

        self.assertTrue(outcome.used_fallback)
        self.assertEqual(outcome.selected_index, 1)

    def test_valid_action_index_is_used(self):
        engine = LLMDecisionEngine(provider=FakeProvider("test-model", '{"action_index": 0}'))
        actions = [{"a": 1}, {"a": 2}]

        outcome = engine.decide_action(
            decision_name="x",
            state={},
            legal_actions=actions,
            prompt_variant="compact_json",
            fallback_index=1,
        )

        self.assertFalse(outcome.used_fallback)
        self.assertEqual(outcome.selected_index, 0)

    def test_invalid_json_uses_fallback(self):
        engine = LLMDecisionEngine(provider=FakeProvider("test-model", "not-json"))
        actions = [{"a": 1}, {"a": 2}]

        outcome = engine.decide_action(
            decision_name="x",
            state={},
            legal_actions=actions,
            prompt_variant="compact_json",
            fallback_index=1,
        )

        self.assertTrue(outcome.used_fallback)
        self.assertEqual(outcome.selected_index, 1)


if __name__ == "__main__":
    unittest.main()
