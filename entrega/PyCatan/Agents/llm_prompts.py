from __future__ import annotations

import json
from typing import Dict, List, Tuple


PROMPT_VARIANTS = {
    "compact_json": (
        "Choose the best legal Catan action to maximize near-term winning chances.",
        "Keep output JSON-only and do not include explanations.",
    ),
    "resource_focus": (
        "Choose the legal action that best improves resource balance for future builds.",
        "Prioritize actions that reduce key shortages and improve production consistency.",
    ),
    "safe_legal": (
        "Choose a valid conservative action; avoid fragile or high-variance moves.",
        "When uncertain, pick the safest legal action with stable value.",
    ),
}


def build_llm_messages(
    decision_name: str,
    state: Dict,
    legal_actions: List[Dict],
    variant: str,
) -> Tuple[str, str]:
    header, guidance = PROMPT_VARIANTS.get(variant, PROMPT_VARIANTS["compact_json"])

    system_prompt = (
        "You are a deterministic Catan policy assistant. Return only one JSON object. "
        "The JSON schema is exactly: "
        '{"action_index": <integer>, "confidence": <number optional>}. '
        "Do not repeat the input, do not use markdown, and do not add explanations."
    )

    max_index = len(legal_actions) - 1
    valid_indexes = ", ".join(str(index) for index in range(len(legal_actions)))
    state_json = json.dumps(state, separators=(",", ":"), ensure_ascii=True)
    indexed_actions = [
        {"action_index": index, "action": action}
        for index, action in enumerate(legal_actions)
    ]
    actions_json = json.dumps(indexed_actions, separators=(",", ":"), ensure_ascii=True)

    # Text labels keep small local models from copying a full JSON payload as the answer.
    user_prompt = "\n".join(
        [
            "TASK: Choose one legal Catan action by index.",
            f"DECISION_NAME: {decision_name}",
            f"GOAL: {header}",
            f"GUIDANCE: {guidance}",
            f"VALID_INDEXES: {valid_indexes}",
            f"INDEX_RANGE: 0..{max_index}",
            f"STATE_JSON: {state_json}",
            f"INDEXED_LEGAL_ACTIONS_JSON: {actions_json}",
            'OUTPUT_JSON_ONLY_EXAMPLE: {"action_index": 0}',
            "CONSTRAINT: action_index must be one of VALID_INDEXES.",
            "CONSTRAINT: action_index is the small list index, not node_id, road_to, or building.",
            "CONSTRAINT: never invent actions outside INDEXED_LEGAL_ACTIONS_JSON.",
        ]
    )
    return system_prompt, user_prompt
