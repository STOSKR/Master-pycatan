# Architecture

**Analysis Date:** 2026-04-15

## Pattern Overview

**Overall:** Layered object-oriented simulation with callback-driven AI agents.

**Key Characteristics:**
- `GameDirector` orchestrates rounds/phases and writes traces (`PyCatan/Managers/GameDirector.py`).
- `GameManager` centralizes mutable game rules/state (`PyCatan/Managers/GameManager.py`).
- Agents implement a shared callback contract via `AgentInterface` (`PyCatan/Interfaces/AgentInterface.py`).

## Layers

**Orchestration Layer:**
- Purpose: Controls game lifecycle and per-turn phase flow.
- Location: `PyCatan/Managers/GameDirector.py`
- Contains: `game_start`, `round_start`, `start_turn`, `start_commerce_phase`, `start_build_phase`, `end_turn`.
- Depends on: `GameManager`, `TraceLoader`.
- Used by: `PyCatan/main.py`, benchmark scripts.

**Rules/State Layer:**
- Purpose: Implements all actionable rules and player/board mutations.
- Location: `PyCatan/Managers/GameManager.py`, `PyCatan/Managers/CommerceManager.py`, `PyCatan/Managers/TurnManager.py`, `PyCatan/Managers/AgentManager.py`
- Contains: building logic, card logic, trading, thief handling, turn counters.
- Depends on: `Classes/*`, agent callbacks.
- Used by: `GameDirector`.

**Domain Model Layer:**
- Purpose: Represents board/resources/cards/constants/offers.
- Location: `PyCatan/Classes/*.py`
- Contains: `Board`, `Hand`, `Materials`, `DevelopmentDeck`, `TradeOffer`, constants.
- Depends on: Python stdlib only.
- Used by: managers and agents.

**Agent Strategy Layer:**
- Purpose: AI decision-making via callback methods.
- Location: `PyCatan/Agents/*.py`, `PyCatan/Interfaces/AgentInterface.py`
- Contains: strategy implementations and helper utilities.
- Depends on: board/resource models and interface contract.
- Used by: `AgentManager` and benchmark scripts.

**Trace/Benchmark/Visualization Layer:**
- Purpose: Persist traces, run large simulations, inspect outcomes.
- Location: `PyCatan/TraceLoader/TraceLoader.py`, `benchmark_vs_random.py`, `benchmark_vs_agentes_estandar.py`, `PyCatan/Visualizer/*`
- Contains: JSON trace export, multiprocessing benchmarks, browser visualizer.
- Depends on: `GameDirector`, local filesystem, browser CDN libs.
- Used by: developers/research workflow.

## Data Flow

**Simulation Flow:**

1. Entry point builds `GameDirector` (`PyCatan/main.py` or benchmark scripts).
2. `GameDirector.game_start` resets state, performs initial placement sequence, and enters round loop.
3. `GameDirector` executes start/commercial/build/end turn phases while `GameManager` calls agent callbacks and mutates board/resources.

**State Management:**
- In-memory mutable dictionaries/lists for board and player state (`GameManager`, `Board`, `AgentManager`).
- Trace snapshots accumulated in `TraceLoader.current_trace` and optionally written as JSON files.

## Key Abstractions

**Agent Callback Contract:**
- Purpose: Defines every decision point custom agents must implement.
- Examples: `PyCatan/Interfaces/AgentInterface.py`, `PyCatan/Agents/RandomAgent.py`
- Pattern: `on_*` methods returning typed dict/object/None depending phase.

**Board Graph Model:**
- Purpose: Encodes nodes, adjacency, roads, ownership, terrain probabilities.
- Examples: `PyCatan/Classes/Board.py`
- Pattern: Validation + mutation methods return `{'response': bool, 'error_msg': str}`.

## Entry Points

**CLI Game Runner:**
- Location: `PyCatan/main.py`
- Triggers: Manual execution.
- Responsibilities: Prompt game count and run sequential games.

**Benchmark Runners:**
- Location: `benchmark_vs_random.py`, `benchmark_vs_agentes_estandar.py`
- Triggers: Manual script execution.
- Responsibilities: Parallel match simulation and CSV summary generation.

**Visualizer:**
- Location: `PyCatan/Visualizer/index.html`
- Triggers: Browser open + JSON trace upload.
- Responsibilities: Render board state and turn progression from traces.

## Error Handling

**Strategy:** Return-value-based validation with fallback behavior.

**Patterns:**
- Rule methods return dicts with `response/error_msg` instead of raising (`Board.py`, `GameManager.py`).
- Broad exception capture in benchmark simulation to keep long runs alive (`benchmark_vs_random.py`, `benchmark_vs_agentes_estandar.py`).

## Cross-Cutting Concerns

**Logging:** Primarily `print` and occasional traceback dumps.
**Validation:** Explicit checks in board/build/trade methods and defensive fallback random choices.
**Authentication:** Not applicable.

---

*Architecture analysis: 2026-04-15*
