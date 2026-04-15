# Coding Conventions

**Analysis Date:** 2026-04-15

## Naming Patterns

**Files:**
- Core modules and agents use PascalCase filenames (`GameManager.py`, `Board.py`, `RandomAgent.py`).
- Tests and benchmark scripts use snake_case (`test_game_manager.py`, `benchmark_vs_random.py`).

**Functions:**
- snake_case for methods and functions (`on_build_phase`, `build_phase_object`, `simulate_match`).

**Variables:**
- snake_case (`workers_a_utilizar`, `game_trace`, `victory_points`).

**Types:**
- Classes and NamedTuple types use PascalCase (`GameDirector`, `Materials`, `TradeOffer`, `Mat`).

## Code Style

**Formatting:**
- Tool used: Not detected (no `black`, `ruff`, `isort`, `autopep8`, or config files).
- Key settings: 4-space indentation, frequent Spanish inline comments/docstrings.

**Linting:**
- Tool used: Not detected.
- Key rules: Not enforced by config.

## Import Organization

**Order:**
1. Python stdlib imports (`random`, `copy`, `math`, `concurrent.futures`).
2. Project imports (`from PyCatan...`, or in some files `from Classes...`/`from Agents...`).
3. Local helper imports (`from .helpers import *` in `PyCatan/Agents/EdoAgent.py`).

**Path Aliases:**
- No formal alias mechanism.
- Mixed absolute import styles exist; use `from PyCatan...` for new code to reduce runtime path ambiguity.

## Error Handling

**Patterns:**
- Domain operations return `{ 'response': bool, 'error_msg': str }` (`PyCatan/Classes/Board.py`, `PyCatan/Managers/GameManager.py`).
- Long-running benchmark workers wrap simulation in broad `try/except` and return fallback tuple (`benchmark_vs_random.py`, `benchmark_vs_agentes_estandar.py`).

## Logging

**Framework:** `print` + optional `traceback.format_exc()`.

**Patterns:**
- Console progress and exception traces in benchmarks.
- Minimal structured logging in managers.

## Comments

**When to Comment:**
- Comments are used to explain game-rule rationale, fallback behavior, and test setup assumptions.

**JSDoc/TSDoc:**
- Not applicable.
- Python docstrings are common in classes/managers; language is predominantly Spanish.

## Function Design

**Size:**
- Orchestration/rules functions can be large and multi-branch (for example `play_development_card` in `PyCatan/Managers/GameManager.py`).

**Parameters:**
- Callback-style signatures in agents (`on_*` methods) often accept board snapshots and return dict/object/None.

**Return Values:**
- Prefer explicit dict payloads with status fields in game logic.
- Agent callbacks return constrained union-like values (`None`, dict, `TradeOffer`, `DevelopmentCard`).

## Module Design

**Exports:**
- Primarily class-per-file modules with direct imports.

**Barrel Files:**
- `__init__.py` files exist but are mostly empty; no strong re-export pattern detected.

---

*Convention analysis: 2026-04-15*
