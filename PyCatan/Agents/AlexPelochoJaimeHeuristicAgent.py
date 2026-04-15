from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

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
from PyCatan.Interfaces.AgentInterface import AgentInterface


@dataclass
class AgentBehaviorConfig:
    max_commerce_actions_per_turn: int = 2


class AlexPelochoJaimeHeuristicAgent(AgentInterface):
    """Heuristic-first agent with reusable decision logic for Part 1."""

    def __init__(self, agent_id: int, config: Optional[AgentBehaviorConfig] = None):
        super().__init__(agent_id)
        self.config = config or AgentBehaviorConfig()
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

    def on_trade_offer(self, board_instance, offer=TradeOffer(), player_id=int):
        self.board = board_instance
        receives_value = self._trade_value(offer.gives)
        gives_value = self._trade_value(offer.receives)

        # Accept only when we gain clear expected value for the current build plan.
        return receives_value >= gives_value + 2

    def on_turn_start(self):
        self._commerce_actions_this_turn = 0
        return None

    def on_turn_end(self):
        for idx, card in enumerate(self.development_cards_hand.hand):
            if card.type == DevelopmentCardConstants.VICTORY_POINT:
                return self.development_cards_hand.select_card(idx)
        return None

    def on_having_more_than_7_materials_when_thief_is_called(self):
        return self.hand

    def on_moving_thief(self):
        return choose_thief_target(self.board, self.id)

    def on_commerce_phase(self):
        if self._commerce_actions_this_turn >= self.config.max_commerce_actions_per_turn:
            return None

        target_building = self._goal_for_current_state()
        trade = choose_bank_trade(self.board, self.id, self.hand.resources, target_building)
        if trade is None:
            return None

        self._commerce_actions_this_turn += 1
        return trade

    def on_build_phase(self, board_instance):
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

    def on_game_start(self, board_instance):
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

    def on_monopoly_card_use(self):
        return choose_material_for_monopoly(self.hand.resources)

    def on_road_building_card_use(self):
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

    def on_year_of_plenty_card_use(self):
        return choose_materials_for_year_of_plenty(self.hand.resources)
