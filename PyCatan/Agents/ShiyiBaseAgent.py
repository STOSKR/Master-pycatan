from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from PyCatan.Agents.RandomAgent import RandomAgent
from PyCatan.Agents.heuristic_core import (
    HeuristicWeights,
    choose_bank_trade,
    choose_best_node,
    choose_best_road,
    choose_best_starting_road,
    choose_material_for_monopoly,
    choose_materials_for_year_of_plenty,
    choose_target_building,
    choose_thief_target,
    positive_shortage,
)
from PyCatan.Classes.Constants import BuildConstants, DevelopmentCardConstants
from PyCatan.Classes.TradeOffer import TradeOffer


@dataclass
class AgentBehaviorConfig:
    max_commerce_actions_per_turn: int = 2


@dataclass
class IncrementalFeatureFlags:
    on_game_start: bool = True
    on_build_phase: bool = True
    on_commerce_phase: bool = True
    on_moving_thief: bool = True

    @classmethod
    def random_baseline(cls) -> "IncrementalFeatureFlags":
        return cls(
            on_game_start=False,
            on_build_phase=False,
            on_commerce_phase=False,
            on_moving_thief=False,
        )

    @classmethod
    def from_dict(cls, payload: Dict[str, bool]) -> "IncrementalFeatureFlags":
        defaults = cls()
        for key in ("on_game_start", "on_build_phase", "on_commerce_phase", "on_moving_thief"):
            if key in payload:
                setattr(defaults, key, bool(payload[key]))
        return defaults


class ShiyiBaseAgent(RandomAgent):
    """
    Incremental trunk agent:
    - Inherits from RandomAgent.
    - Enables heuristic decisions through feature flags.
    - Falls back to random behavior on disabled features or runtime issues.
    """

    def __init__(
        self,
        agent_id: int,
        config: Optional[AgentBehaviorConfig | Dict[str, int]] = None,
        feature_flags: Optional[IncrementalFeatureFlags | Dict[str, bool]] = None,
    ):
        super().__init__(agent_id)
        if isinstance(config, dict):
            self.config = AgentBehaviorConfig(**config)
        else:
            self.config = config or AgentBehaviorConfig()
        if feature_flags is None:
            self.feature_flags = IncrementalFeatureFlags()
        elif isinstance(feature_flags, dict):
            self.feature_flags = IncrementalFeatureFlags.from_dict(feature_flags)
        else:
            self.feature_flags = feature_flags

        self.weights = HeuristicWeights()
        self._commerce_actions_this_turn = 0

    def _resource_priority(self) -> Dict[int, int]:
        city_shortage = positive_shortage(self.hand.resources, BuildConstants.CITY)
        town_shortage = positive_shortage(self.hand.resources, BuildConstants.TOWN)
        return {
            material_id: 1 + city_shortage[material_id] * 3 + town_shortage[material_id] * 2
            for material_id in range(5)
        }

    def _trade_value(self, materials) -> int:
        priority = self._resource_priority()
        return sum(priority[material_id] * materials[material_id] for material_id in range(5))

    def _goal_for_current_state(self) -> str:
        return choose_target_building(
            resources=self.hand.resources,
            has_city_nodes=bool(self.board.valid_city_nodes(self.id)),
            has_town_nodes=bool(self.board.valid_town_nodes(self.id)),
            has_road_nodes=bool(self.board.valid_road_nodes(self.id)),
        )

    def on_turn_start(self):
        self._commerce_actions_this_turn = 0
        return super().on_turn_start()

    def on_trade_offer(self, board_instance, offer=TradeOffer(), player_id=int):
        if not self.feature_flags.on_commerce_phase:
            return super().on_trade_offer(board_instance, offer, player_id)

        try:
            self.board = board_instance
            receives_value = self._trade_value(offer.gives)
            gives_value = self._trade_value(offer.receives)
            return receives_value >= gives_value + 2
        except Exception:
            return super().on_trade_offer(board_instance, offer, player_id)

    def on_commerce_phase(self):
        if not self.feature_flags.on_commerce_phase:
            return super().on_commerce_phase()

        try:
            if self._commerce_actions_this_turn >= self.config.max_commerce_actions_per_turn:
                return None
            if not hasattr(self, "board") or self.board is None:
                return super().on_commerce_phase()

            target_building = self._goal_for_current_state()
            trade = choose_bank_trade(self.board, self.id, self.hand.resources, target_building)
            if trade is None:
                return None

            self._commerce_actions_this_turn += 1
            return trade
        except Exception:
            return super().on_commerce_phase()

    def on_build_phase(self, board_instance):
        if not self.feature_flags.on_build_phase:
            return super().on_build_phase(board_instance)

        try:
            self.board = board_instance

            if self.hand.resources.has_more(BuildConstants.CITY):
                city_nodes = self.board.valid_city_nodes(self.id)
                best_city = choose_best_node(self.board, city_nodes, self.weights)
                if best_city is not None:
                    return {"building": BuildConstants.CITY, "node_id": best_city}

            if self.hand.resources.has_more(BuildConstants.TOWN):
                town_nodes = self.board.valid_town_nodes(self.id)
                best_town = choose_best_node(self.board, town_nodes, self.weights)
                if best_town is not None:
                    return {"building": BuildConstants.TOWN, "node_id": best_town}

            if self.hand.resources.has_more(BuildConstants.ROAD):
                road_nodes = self.board.valid_road_nodes(self.id)
                best_road = choose_best_road(self.board, self.id, road_nodes, self.weights)
                if best_road is not None:
                    return {
                        "building": BuildConstants.ROAD,
                        "node_id": best_road["starting_node"],
                        "road_to": best_road["finishing_node"],
                    }

            if self.hand.resources.has_more(BuildConstants.CARD):
                return {"building": BuildConstants.CARD}

            return None
        except Exception:
            return super().on_build_phase(board_instance)

    def on_game_start(self, board_instance):
        if not self.feature_flags.on_game_start:
            return super().on_game_start(board_instance)

        try:
            self.board = board_instance
            valid_nodes = self.board.valid_starting_nodes()
            best_node = choose_best_node(self.board, valid_nodes, self.weights)
            if best_node is None:
                return super().on_game_start(board_instance)

            best_road = choose_best_starting_road(self.board, best_node, self.weights)
            if best_road is None:
                adjacent = self.board.nodes[best_node]["adjacent"]
                if not adjacent:
                    return super().on_game_start(board_instance)
                best_road = adjacent[0]

            return int(best_node), int(best_road)
        except Exception:
            return super().on_game_start(board_instance)

    def on_turn_end(self):
        if not self.feature_flags.on_moving_thief:
            return super().on_turn_end()

        try:
            for idx, card in enumerate(self.development_cards_hand.hand):
                if card.type == DevelopmentCardConstants.VICTORY_POINT:
                    return self.development_cards_hand.select_card(idx)
            return super().on_turn_end()
        except Exception:
            return super().on_turn_end()

    def on_moving_thief(self):
        if not self.feature_flags.on_moving_thief:
            return super().on_moving_thief()

        try:
            return choose_thief_target(self.board, self.id)
        except Exception:
            return super().on_moving_thief()

    def on_monopoly_card_use(self):
        if not self.feature_flags.on_moving_thief:
            return super().on_monopoly_card_use()
        try:
            return choose_material_for_monopoly(self.hand.resources)
        except Exception:
            return super().on_monopoly_card_use()

    def on_road_building_card_use(self):
        if not self.feature_flags.on_moving_thief:
            return super().on_road_building_card_use()

        try:
            road_options = self.board.valid_road_nodes(self.id)
            first = choose_best_road(self.board, self.id, road_options, self.weights)
            if first is None:
                return None

            remaining = [
                option
                for option in road_options
                if not (
                    option["starting_node"] == first["starting_node"]
                    and option["finishing_node"] == first["finishing_node"]
                )
            ]
            second = choose_best_road(self.board, self.id, remaining, self.weights)
            return {
                "node_id": first["starting_node"],
                "road_to": first["finishing_node"],
                "node_id_2": None if second is None else second["starting_node"],
                "road_to_2": None if second is None else second["finishing_node"],
            }
        except Exception:
            return super().on_road_building_card_use()

    def on_year_of_plenty_card_use(self):
        if not self.feature_flags.on_moving_thief:
            return super().on_year_of_plenty_card_use()
        try:
            return choose_materials_for_year_of_plenty(self.hand.resources)
        except Exception:
            return super().on_year_of_plenty_card_use()
