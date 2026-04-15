# Codebase Concerns

**Analysis Date:** 2026-04-15

## Tech Debt

**Import Path Inconsistency:**
- Issue: Mixed import roots (`from PyCatan...` vs `from Classes/Agents/Managers...`) across agents and benchmark scripts.
- Files: `PyCatan/Agents/AlexPelochoJaimeAgent.py`, `PyCatan/Agents/CrabisaAgent.py`, `PyCatan/Agents/helpers.py`, `benchmark_vs_random.py`, `benchmark_vs_agentes_estandar.py`.
- Impact: Execution depends on cwd/PYTHONPATH; root benchmark runs are fragile and can raise `ModuleNotFoundError`.
- Fix approach: Normalize all internal imports to `from PyCatan...` and run via consistent module entry points.

**Monolithic Rule Engine:**
- Issue: Central rule logic is concentrated in very large files.
- Files: `PyCatan/Managers/GameManager.py` (946 lines), `PyCatan/Classes/Board.py` (465 lines).
- Impact: High coupling, difficult debugging/refactoring, higher regression risk during feature changes.
- Fix approach: Extract card effects, trading, and board-path utilities into smaller focused modules with targeted tests.

## Known Bugs

**Road-Building Fallback Indexing Bug Risk:**
- Symptoms: Potential type/index error when fallback road selection is triggered during development-card road placement.
- Files: `PyCatan/Managers/GameManager.py` (road-building effect branch inside `play_development_card`).
- Trigger: `valid_nodes` element chosen via `random.choice(valid_nodes)` then reused as list index in `valid_nodes[road_node]`.
- Workaround: Use guaranteed-valid road choices in agents; avoid forcing fallback path.

## Security Considerations

**Local Secret Hygiene:**
- Risk: `.env` exists in repository root; accidental sharing remains possible outside git ignore workflows.
- Files: `.env`, `.gitignore`.
- Current mitigation: `.gitignore` includes `.env`.
- Recommendations: Add `.env.example` and document required keys without values; keep benchmark output paths separate from sensitive local files.

## Performance Bottlenecks

**Permutation Benchmark Explosion:**
- Problem: Standard benchmark computes permutations of benchmark agents and runs many process-pooled matches.
- Files: `benchmark_vs_agentes_estandar.py`.
- Cause: `itertools.permutations(BENCHMARK_AGENTS, 3)` with per-position/per-match loops and large batch futures.
- Improvement path: Add sampling mode, deterministic seed subsets, and configurable max permutations.

## Fragile Areas

**Dirty Worktree + Bench/Agent Edits:**
- Files: `PyCatan/Agents/AlexPelochoJaimeAgent.py`, `PyCatan/Agents/CrabisaAgent.py`, `PyCatan/Agents/PabloAleixAlexAgent.py`, `PyCatan/Agents/SigmaAgent.py`, `benchmark_vs_agentes_estandar.py`, `benchmark_vs_random.py`.
- Why fragile: Active local edits in strategy/benchmark files make baseline behavior non-reproducible.
- Safe modification: Branch before benchmarking, commit/stash in-progress changes, and record exact commit hash for any comparison run.
- Test coverage: Agent-specific behavior coverage is thin; benchmark scripts are not directly unit tested.

## Scaling Limits

**Trace Fixture Growth:**
- Current capacity: 100 committed trace fixtures in `PyCatan/Tests/test_traces/`.
- Limit: Repository size and test I/O cost increase quickly as fixtures grow.
- Scaling path: Keep a compact golden subset + generate extended traces as optional artifacts in CI/local runs.

## Dependencies at Risk

**Unpinned Python Tooling:**
- Risk: No declared dependency manifests (`requirements.txt`/`pyproject.toml` absent).
- Impact: Onboarding inconsistency; test command fails in clean environments (observed: `No module named pytest`).
- Migration plan: Add pinned runtime/dev dependency files and a minimal bootstrap command in `PyCatan/README.md`.

## Missing Critical Features

**Packaging/Execution Standardization:**
- Problem: No canonical install/run method for agents, benchmarks, and tests.
- Blocks: Reliable CI setup and reproducible cross-machine benchmark results.

## Test Coverage Gaps

**Agent and Benchmark Behavior:**
- What's not tested: Most custom agent strategies and both root benchmark scripts.
- Files: `PyCatan/Agents/*.py` (except behavior indirectly via game-level tests), `benchmark_vs_random.py`, `benchmark_vs_agentes_estandar.py`.
- Risk: Strategy regressions or benchmark orchestration bugs can ship unnoticed.
- Priority: High.

---

*Concerns audit: 2026-04-15*
