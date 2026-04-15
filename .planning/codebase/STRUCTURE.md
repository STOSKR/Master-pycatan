# Codebase Structure

**Analysis Date:** 2026-04-15

## Directory Layout

```
Master-pycatan/
|- benchmark_vs_random.py                # Benchmark: target agent vs RandomAgent
|- benchmark_vs_agentes_estandar.py      # Benchmark: target agent vs standard agent pool
|- PyCatan/
|  |- Agents/                            # Agent strategies + helper utilities
|  |- Classes/                           # Core domain models (board, resources, cards)
|  |- Interfaces/                        # Agent contract definitions
|  |- Managers/                          # Orchestration and game rule managers
|  |- TraceLoader/                       # JSON trace writer
|  |- Tests/                             # Unit/integration tests + trace fixtures
|  |- Visualizer/                        # Static HTML/JS/CSS trace viewer
|  |- main.py                            # Interactive CLI runner
|  \- README.md                          # Project usage overview
\- .planning/codebase/                   # Generated mapping documents
```

## Directory Purposes

**`PyCatan/Agents`:**
- Purpose: Custom AI decision logic.
- Contains: Agent classes inheriting `AgentInterface`, plus shared heuristics in `helpers.py`.
- Key files: `PyCatan/Agents/RandomAgent.py`, `PyCatan/Agents/TristanAgent.py`, `PyCatan/Agents/helpers.py`.

**`PyCatan/Managers`:**
- Purpose: Game flow and state mutation orchestration.
- Contains: Director/manager classes for turns, commerce, player loading.
- Key files: `PyCatan/Managers/GameDirector.py`, `PyCatan/Managers/GameManager.py`.

**`PyCatan/Classes`:**
- Purpose: Domain entities and constants used by managers/agents.
- Contains: `Board`, `Materials`, `Hand`, development cards, constants, trade offer.
- Key files: `PyCatan/Classes/Board.py`, `PyCatan/Classes/Materials.py`, `PyCatan/Classes/Constants.py`.

**`PyCatan/Tests`:**
- Purpose: Regression checks for classes/managers and trace comparison.
- Contains: `test_*.py` files and fixture traces.
- Key files: `PyCatan/Tests/test_game_manager.py`, `PyCatan/Tests/test_board.py`, `PyCatan/Tests/test_trace_comparison.py`.

## Key File Locations

**Entry Points:**
- `PyCatan/main.py`: Manual game-loop runner.
- `benchmark_vs_random.py`: Parallel benchmark against RandomAgent.
- `benchmark_vs_agentes_estandar.py`: Parallel benchmark against standard agent permutations.

**Configuration:**
- `.gitignore`: Currently only ignores `.env`.
- `PyCatan/README.md`: Setup/usage instructions.

**Core Logic:**
- `PyCatan/Managers/GameManager.py`: Most game rules and action dispatch.
- `PyCatan/Managers/GameDirector.py`: Phase orchestration and trace composition.

**Testing:**
- `PyCatan/Tests/*.py`: Test modules.
- `PyCatan/Tests/test_traces/*.json`: 100 committed trace fixtures.

## Naming Conventions

**Files:**
- Core/agent modules: PascalCase filenames (`GameManager.py`, `RandomAgent.py`).
- Tests/benchmarks: snake_case filenames (`test_game_manager.py`, `benchmark_vs_random.py`).

**Directories:**
- PascalCase/Title-like in core package (`Agents`, `Classes`, `Managers`, `Interfaces`, `TraceLoader`, `Visualizer`, `Tests`).

## Where to Add New Code

**New Feature (agent behavior):**
- Primary code: `PyCatan/Agents/<YourAgentName>Agent.py` inheriting `AgentInterface`.
- Tests: `PyCatan/Tests/test_<agent_or_behavior>.py` (focus on callback outputs under controlled board states).

**New Component/Module:**
- Game-rule additions: `PyCatan/Managers/` (or split from `GameManager.py` if behavior is large).
- New model types: `PyCatan/Classes/`.

**Utilities:**
- Shared agent heuristics: `PyCatan/Agents/helpers.py` or a new utility module in `PyCatan/Agents/`.

## Special Directories

**`PyCatan/Tests/test_traces`:**
- Purpose: Deterministic game trace fixtures for regression comparison.
- Generated: No (stored fixtures).
- Committed: Yes.

**`PyCatan/TraceLoader/Traces` (runtime-created):**
- Purpose: Timestamped output traces written by `TraceLoader`.
- Generated: Yes.
- Committed: Not detected in current tree.

**Import Path Caveat:**
- The repo mixes `from PyCatan...` imports with bare `from Classes/Agents/Managers...` imports.
- For new modules, prefer `from PyCatan...` to reduce cwd/PYTHONPATH fragility, especially for root-level benchmark scripts.

---

*Structure analysis: 2026-04-15*
