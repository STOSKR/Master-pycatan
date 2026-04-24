from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from PyCatan.Agents.ShiyiHeuristicAgent import AgentBehaviorConfig, ShiyiHeuristicAgent
from PyCatan.Agents.heuristic_core import road_score, settlement_score
from PyCatan.Agents.llm_engine import (
    BaseLLMProvider,
    DecisionOutcome,
    LLMDecisionEngine,
    ProviderError,
    build_provider_from_env,
)
from PyCatan.Classes.Constants import BuildConstants


END_BUILD_ACTION = "__END_BUILD__"


@dataclass
class LLMBehaviorConfig:
    enable_on_game_start: bool = True
    enable_on_build_phase: bool = True
    prompt_variant_on_game_start: str = "compact_json"
    prompt_variant_on_build_phase: str = "resource_focus"
    max_actions_on_game_start: int = 14
    max_actions_on_build_phase: int = 14
    decision_timeout_seconds: float = 8.0


class ShiyiLLMAgent(ShiyiHeuristicAgent):
    """LLM-assisted agent that falls back to deterministic heuristics safely."""

    def __init__(
        self,
        agent_id: int,
        behavior_config: Optional[AgentBehaviorConfig | Dict[str, Any]] = None,
        llm_config: Optional[LLMBehaviorConfig | Dict[str, Any]] = None,
        provider: Optional[BaseLLMProvider] = None,
    ):
        if isinstance(behavior_config, dict):
            behavior_config = AgentBehaviorConfig(**behavior_config)
        if isinstance(llm_config, dict):
            llm_config = LLMBehaviorConfig(**llm_config)

        super().__init__(agent_id=agent_id, config=behavior_config)
        self.llm_config = llm_config or LLMBehaviorConfig()
        self.llm_init_error: Optional[str] = None
        self.decision_history: List[Dict[str, Any]] = []

        if provider is None:
            try:
                provider = build_provider_from_env()
            except Exception as exc:
                self.llm_init_error = str(exc)
                provider = None

        self.decision_engine = LLMDecisionEngine(
            provider=provider,
            default_timeout_seconds=self.llm_config.decision_timeout_seconds,
        )

    def get_llm_decision_history(self) -> List[Dict[str, Any]]:
        return list(self.decision_history)

    def _record_decision(self, outcome: DecisionOutcome) -> None:
        self.decision_history.append(
            {
                "decision": outcome.decision_name,
                "provider": outcome.provider,
                "model": outcome.model,
                "prompt_variant": outcome.prompt_variant,
                "latency_ms": outcome.latency_ms,
                "fallback": outcome.used_fallback,
                "reason": outcome.reason,
                "selected_index": outcome.selected_index,
                "raw_response_preview": outcome.raw_response[:500],
                "input_tokens": outcome.input_tokens,
                "output_tokens": outcome.output_tokens,
            }
        )

    @staticmethod
    def _action_key(action: Dict[str, Any]) -> str:
        return json.dumps(action, sort_keys=True, separators=(",", ":"))

    def _starting_actions(self, max_actions: int) -> List[Dict[str, int]]:
        actions_with_scores: List[Tuple[float, Dict[str, int]]] = []

        for node_id in self.board.valid_starting_nodes():
            node_score = settlement_score(self.board, node_id, self.weights)
            for road_to in self.board.nodes[node_id]["adjacent"]:
                road_score_hint = settlement_score(self.board, road_to, self.weights)
                score = node_score * 1.0 + road_score_hint * 0.35
                actions_with_scores.append((score, {"node_id": node_id, "road_to": road_to}))

        actions_with_scores.sort(
            key=lambda item: (-item[0], item[1]["node_id"], item[1]["road_to"])
        )

        return [action for _, action in actions_with_scores[:max_actions]]

    def _build_actions(self, max_actions: int) -> List[Dict[str, Any]]:
        actions_with_scores: List[Tuple[float, Dict[str, Any]]] = []

        if self.hand.resources.has_more(BuildConstants.CITY):
            for node_id in self.board.valid_city_nodes(self.id):
                score = settlement_score(self.board, node_id, self.weights) + 10.0
                actions_with_scores.append(
                    (score, {"building": BuildConstants.CITY, "node_id": node_id})
                )

        if self.hand.resources.has_more(BuildConstants.TOWN):
            for node_id in self.board.valid_town_nodes(self.id):
                score = settlement_score(self.board, node_id, self.weights) + 8.0
                actions_with_scores.append(
                    (score, {"building": BuildConstants.TOWN, "node_id": node_id})
                )

        if self.hand.resources.has_more(BuildConstants.ROAD):
            valid_town_nodes = self.board.valid_town_nodes(self.id)
            for option in self.board.valid_road_nodes(self.id):
                score = road_score(
                    self.board,
                    self.id,
                    option,
                    self.weights,
                    valid_town_nodes=valid_town_nodes,
                ) + 5.0
                actions_with_scores.append(
                    (
                        score,
                        {
                            "building": BuildConstants.ROAD,
                            "node_id": option["starting_node"],
                            "road_to": option["finishing_node"],
                        },
                    )
                )

        if self.hand.resources.has_more(BuildConstants.CARD):
            actions_with_scores.append((2.5, {"building": BuildConstants.CARD}))

        actions_with_scores.append((-1.0, {"building": END_BUILD_ACTION}))

        actions_with_scores.sort(
            key=lambda item: (
                -item[0],
                item[1].get("building", ""),
                item[1].get("node_id", -1),
                item[1].get("road_to", -1),
            )
        )

        return [action for _, action in actions_with_scores[:max_actions]]

    def on_game_start(self, board_instance):
        heuristic_node, heuristic_road = super().on_game_start(board_instance)

        if not (self.llm_config.enable_on_game_start and self.decision_engine.is_enabled):
            return heuristic_node, heuristic_road

        legal_actions = self._starting_actions(self.llm_config.max_actions_on_game_start)
        if not legal_actions:
            return heuristic_node, heuristic_road

        fallback_action = {"node_id": heuristic_node, "road_to": heuristic_road}
        fallback_key = self._action_key(fallback_action)
        action_keys = [self._action_key(action) for action in legal_actions]

        if fallback_key in action_keys:
            fallback_index = action_keys.index(fallback_key)
        else:
            legal_actions.insert(0, fallback_action)
            fallback_index = 0

        state = {
            "player_id": self.id,
            "resources": self.hand.resources.__to_object__(),
            "initial_settlement_required": True,
            "llm_init_error": self.llm_init_error,
        }

        outcome = self.decision_engine.decide_action(
            decision_name="on_game_start",
            state=state,
            legal_actions=legal_actions,
            prompt_variant=self.llm_config.prompt_variant_on_game_start,
            fallback_index=fallback_index,
            timeout_seconds=self.llm_config.decision_timeout_seconds,
        )
        self._record_decision(outcome)

        action = outcome.selected_action
        node_id = action.get("node_id")
        road_to = action.get("road_to")

        if (
            node_id in self.board.valid_starting_nodes()
            and isinstance(road_to, int)
            and road_to in self.board.nodes[node_id]["adjacent"]
        ):
            return node_id, road_to

        return heuristic_node, heuristic_road

    def on_build_phase(self, board_instance):
        heuristic_action = super().on_build_phase(board_instance)

        if not (self.llm_config.enable_on_build_phase and self.decision_engine.is_enabled):
            return heuristic_action

        legal_actions = self._build_actions(self.llm_config.max_actions_on_build_phase)
        if not legal_actions:
            return heuristic_action

        if heuristic_action is None:
            fallback_action = {"building": END_BUILD_ACTION}
        else:
            fallback_action = heuristic_action

        fallback_key = self._action_key(fallback_action)
        action_keys = [self._action_key(action) for action in legal_actions]

        if fallback_key in action_keys:
            fallback_index = action_keys.index(fallback_key)
        else:
            legal_actions.insert(0, fallback_action)
            fallback_index = 0

        state = {
            "player_id": self.id,
            "resources": self.hand.resources.__to_object__(),
            "target_building": self._goal_for_current_state(),
            "llm_init_error": self.llm_init_error,
        }

        outcome = self.decision_engine.decide_action(
            decision_name="on_build_phase",
            state=state,
            legal_actions=legal_actions,
            prompt_variant=self.llm_config.prompt_variant_on_build_phase,
            fallback_index=fallback_index,
            timeout_seconds=self.llm_config.decision_timeout_seconds,
        )
        self._record_decision(outcome)

        action = outcome.selected_action
        if action.get("building") == END_BUILD_ACTION:
            return None

        return action
