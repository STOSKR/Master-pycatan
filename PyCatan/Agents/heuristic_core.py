from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence

from PyCatan.Classes.Board import Board
from PyCatan.Classes.Constants import (
    BuildConstants,
    HarborConstants,
    MaterialConstants,
    TerrainConstants,
)
from PyCatan.Classes.Materials import Materials


RESOURCE_IDS: Sequence[int] = (
    MaterialConstants.CEREAL,
    MaterialConstants.MINERAL,
    MaterialConstants.CLAY,
    MaterialConstants.WOOD,
    MaterialConstants.WOOL,
)

DICE_WEIGHTS: Dict[int, int] = {
    2: 1,
    3: 2,
    4: 3,
    5: 4,
    6: 5,
    7: 6,
    8: 5,
    9: 4,
    10: 3,
    11: 2,
    12: 1,
}

BUILD_COSTS: Dict[str, Materials] = {
    BuildConstants.TOWN: Materials.from_building(BuildConstants.TOWN),
    BuildConstants.CITY: Materials.from_building(BuildConstants.CITY),
    BuildConstants.ROAD: Materials.from_building(BuildConstants.ROAD),
    BuildConstants.CARD: Materials.from_building(BuildConstants.CARD),
}


@dataclass(frozen=True)
class HeuristicWeights:
    production: float = 1.0
    diversity: float = 2.2
    harbor_bonus: float = 1.1
    interior_bonus: float = 0.8
    expansion_bonus: float = 0.6
    road_to_town_bonus: float = 2.0


def positive_shortage(resources: Materials, building: str) -> Materials:
    return (BUILD_COSTS[building] - resources).replace_negative()


def missing_count(resources: Materials, building: str) -> int:
    return sum(positive_shortage(resources, building))


def node_resource_yield(board: Board, node_id: int) -> Dict[int, float]:
    resources = {resource_id: 0.0 for resource_id in RESOURCE_IDS}
    for terrain_id in board.nodes[node_id]["contacting_terrain"]:
        terrain = board.terrain[terrain_id]
        terrain_type = terrain["terrain_type"]
        if terrain_type == TerrainConstants.DESERT:
            continue

        probability = terrain["probability"]
        resources[terrain_type] += float(DICE_WEIGHTS.get(probability, 0))

    return resources


def settlement_score(board: Board, node_id: int, weights: HeuristicWeights) -> float:
    yield_by_resource = node_resource_yield(board, node_id)
    production_score = sum(yield_by_resource.values())
    diversity_score = sum(1 for value in yield_by_resource.values() if value > 0)

    score = (
        weights.production * production_score
        + weights.diversity * diversity_score
    )

    if board.nodes[node_id]["harbor"] != HarborConstants.NONE:
        score += weights.harbor_bonus

    if not board.is_coastal_node(node_id):
        score += weights.interior_bonus

    return score


def choose_best_node(
    board: Board,
    node_ids: Iterable[int],
    weights: HeuristicWeights,
) -> Optional[int]:
    ranked: List[tuple[float, int]] = []
    for node_id in node_ids:
        ranked.append((settlement_score(board, node_id, weights), node_id))

    if not ranked:
        return None

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][1]


def choose_best_starting_road(
    board: Board,
    start_node: int,
    weights: HeuristicWeights,
) -> Optional[int]:
    candidates = board.nodes[start_node]["adjacent"]
    ranked: List[tuple[float, int]] = []

    for node_id in candidates:
        if board.nodes[node_id]["player"] != -1:
            continue

        score = settlement_score(board, node_id, weights)
        score += weights.expansion_bonus * len(board.nodes[node_id]["adjacent"])
        ranked.append((score, node_id))

    if not ranked:
        return None

    ranked.sort(key=lambda item: (-item[0], item[1]))
    return ranked[0][1]


def road_score(
    board: Board,
    player_id: int,
    road_option: Dict[str, int],
    weights: HeuristicWeights,
    valid_town_nodes: Optional[Sequence[int]] = None,
) -> float:
    target = road_option["finishing_node"]
    score = settlement_score(board, target, weights)

    if valid_town_nodes is None:
        valid_town_nodes = board.valid_town_nodes(player_id)

    if target in valid_town_nodes:
        score += weights.road_to_town_bonus

    score += weights.expansion_bonus * len(board.nodes[target]["adjacent"])
    return score


def choose_best_road(
    board: Board,
    player_id: int,
    road_options: Sequence[Dict[str, int]],
    weights: HeuristicWeights,
) -> Optional[Dict[str, int]]:
    valid_town_nodes = board.valid_town_nodes(player_id)
    ranked: List[tuple[float, Dict[str, int]]] = []

    for option in road_options:
        ranked.append((road_score(board, player_id, option, weights, valid_town_nodes), option))

    if not ranked:
        return None

    ranked.sort(
        key=lambda item: (
            -item[0],
            item[1]["starting_node"],
            item[1]["finishing_node"],
        )
    )
    return ranked[0][1]


def choose_target_building(
    resources: Materials,
    has_city_nodes: bool,
    has_town_nodes: bool,
    has_road_nodes: bool,
) -> str:
    city_missing = missing_count(resources, BuildConstants.CITY)
    town_missing = missing_count(resources, BuildConstants.TOWN)
    road_missing = missing_count(resources, BuildConstants.ROAD)

    if has_city_nodes and (city_missing == 0 or city_missing <= 2):
        return BuildConstants.CITY

    if has_town_nodes and (town_missing == 0 or town_missing <= 2):
        return BuildConstants.TOWN

    if has_road_nodes and road_missing <= 1:
        return BuildConstants.ROAD

    return BuildConstants.CARD


def bank_trade_rate(board: Board, player_id: int, material_id: int) -> int:
    harbor = board.check_for_player_harbors(player_id, material_id)
    if harbor == material_id:
        return 2
    if harbor == HarborConstants.ALL:
        return 3
    return 4


def choose_bank_trade(
    board: Board,
    player_id: int,
    resources: Materials,
    target_building: str,
) -> Optional[Dict[str, int]]:
    target_cost = BUILD_COSTS[target_building]
    shortages = (target_cost - resources).replace_negative()
    needed_materials = [idx for idx, amount in enumerate(shortages) if amount > 0]

    if not needed_materials:
        return None

    best_give_material: Optional[int] = None
    best_give_score = -1

    for material_id in RESOURCE_IDS:
        rate = bank_trade_rate(board, player_id, material_id)
        available = resources[material_id]
        reserve = target_cost[material_id]
        surplus = available - reserve

        if surplus < rate:
            continue

        score = surplus - rate
        if score > best_give_score:
            best_give_score = score
            best_give_material = material_id

    if best_give_material is None:
        return None

    needed_materials.sort(key=lambda idx: (-shortages[idx], idx))
    receive_material = needed_materials[0]

    return {"gives": best_give_material, "receives": receive_material}


def choose_material_for_monopoly(resources: Materials) -> int:
    city_shortage = positive_shortage(resources, BuildConstants.CITY)
    town_shortage = positive_shortage(resources, BuildConstants.TOWN)
    road_shortage = positive_shortage(resources, BuildConstants.ROAD)

    weighted_shortage = [
        city_shortage[idx] * 3 + town_shortage[idx] * 2 + road_shortage[idx]
        for idx in RESOURCE_IDS
    ]

    best_index = max(range(len(weighted_shortage)), key=lambda idx: (weighted_shortage[idx], -idx))
    return int(best_index)


def choose_materials_for_year_of_plenty(resources: Materials) -> Dict[str, int]:
    city_shortage = positive_shortage(resources, BuildConstants.CITY)
    town_shortage = positive_shortage(resources, BuildConstants.TOWN)

    weighted_shortage = [
        city_shortage[idx] * 2 + town_shortage[idx]
        for idx in RESOURCE_IDS
    ]

    ranked = sorted(
        range(len(weighted_shortage)),
        key=lambda idx: (-weighted_shortage[idx], idx),
    )

    first = ranked[0]
    second = ranked[1] if len(ranked) > 1 else ranked[0]

    return {"material": int(first), "material_2": int(second)}


def choose_thief_target(board: Board, player_id: int) -> Dict[str, int]:
    best_terrain = None
    best_score = float("-inf")
    best_victim = -1
    current_thief_terrain = 0

    for terrain in board.terrain:
        if terrain["has_thief"]:
            current_thief_terrain = terrain["id"]

    for terrain in board.terrain:
        if terrain["has_thief"] or terrain["terrain_type"] == TerrainConstants.DESERT:
            continue

        own_adjacent = 0
        enemy_adjacent: Dict[int, int] = {}

        for node_id in terrain["contacting_nodes"]:
            owner = board.nodes[node_id]["player"]
            if owner == -1:
                continue
            if owner == player_id:
                own_adjacent += 1
                continue
            enemy_adjacent[owner] = enemy_adjacent.get(owner, 0) + 1

        if not enemy_adjacent:
            continue

        probability_weight = DICE_WEIGHTS.get(terrain["probability"], 0)
        best_enemy = max(enemy_adjacent.items(), key=lambda item: item[1])[0]

        score = probability_weight * 1.5 + sum(enemy_adjacent.values()) * 2 - own_adjacent * 3
        if score > best_score:
            best_score = score
            best_terrain = terrain["id"]
            best_victim = best_enemy

    if best_terrain is None:
        return {"terrain": current_thief_terrain, "player": -1}

    return {"terrain": int(best_terrain), "player": int(best_victim)}
