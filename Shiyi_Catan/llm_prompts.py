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
        "You are a deterministic Catan policy assistant. "
        "You must return only valid JSON with this schema: "
        '{"action_index": <int>, "confidence": <float 0-1 optional>}. '
        "Do not include markdown or additional text."
    )

    payload = {
        "decision_name": decision_name,
        "state": state,
        "legal_actions": legal_actions,
        "instruction": {
            "goal": header,
            "guidance": guidance,
            "constraints": [
                "action_index must point to an existing legal action",
                "never invent actions outside legal_actions",
            ],
        },
    }

    user_prompt = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    return system_prompt, user_prompt
