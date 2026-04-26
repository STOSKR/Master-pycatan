from __future__ import annotations

from typing import Dict, Optional

from PyCatan.Agents.ShiyiBaseAgent import (
    AgentBehaviorConfig,
    IncrementalFeatureFlags,
    ShiyiBaseAgent,
)


class ShiyiHeuristicAgent(ShiyiBaseAgent):
    """
    Heuristic profile built on top of the RandomAgent-derived incremental trunk.
    """

    def __init__(
        self,
        agent_id: int,
        config: Optional[AgentBehaviorConfig] = None,
        feature_flags: Optional[IncrementalFeatureFlags | Dict[str, bool]] = None,
    ):
        super().__init__(agent_id=agent_id, config=config, feature_flags=feature_flags)
