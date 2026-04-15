# Master-pycatan: Catan Agents Assignment (Heuristic + LLM)

## What This Is

This is a university assignment built on an existing PyCatan codebase. The work adds and evaluates two agent tracks: Part 1 (heuristic decision-making) and Part 2 (LLM-assisted decision-making) while keeping compatibility with the current simulation engine and benchmark flow.

## Core Value

Deliver reproducible, evidence-backed comparison of heuristic and LLM agent decisions in the same Catan engine.

## Requirements

### Validated

- ✓ The PyCatan engine runs full Catan matches with callback-based agents via AgentInterface methods — existing.
- ✓ Benchmark scripts at repo root can execute large match batches and export CSV summaries — existing.
- ✓ Existing tests cover core board, manager, and trace behavior — existing.

### Active

- [ ] Deliver Part 1 heuristic agent with benchmark evaluation against random and standard opponents.
- [ ] Deliver Part 2 LLM integration for on_game_start plus one frequent in-game decision.
- [ ] Produce reproducible outputs and assignment report/memory (max 10 pages).

### Out of Scope

- Full cloud deployment or production service hardening — assignment is local/offline simulation.
- Visualizer redesign — no UI feature expansion required for grading.
- Model training/fine-tuning pipelines — assignment scope is prompt + inference integration.

## Context

- Brownfield repository with engine in PyCatan/ and benchmark runners at repo root.
- Existing custom agents already live in PyCatan/Agents/ and are used as comparison baselines.
- Agent callback contract is defined in PyCatan/Interfaces/AgentInterface.py.
- Current benchmark scripts already compute wins, victory points, and rank, but need reproducibility hardening.
- Codebase map identified two critical risks for this assignment: dirty worktree benchmarking and import-path inconsistency.

## Constraints

- **Process**: Strict stage order is mandatory: Investigate/Study -> Plan -> Write code.
- **Code Quality**: New logic must be reusable and clean; avoid one-off hacks.
- **Version Control**: Commit per planned step with clear scope boundaries.
- **LLM Scope**: Required decision points are on_game_start plus one frequent in-game callback.
- **Prompting**: At least 3 prompt variants are required.
- **Model Coverage**: At least 3 models are required across Ollama (local), AWS Bedrock, and UPV API.
- **Reproducibility**: Benchmarks and evaluations must be rerunnable with recorded metadata.
- **Compatibility**: New imports should keep a consistent package style to avoid runtime path issues.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Frequent LLM in-game hook defaults to on_build_phase (pending validation) | High-frequency strategic decision with clear observable impact | — Pending |
| Primary comparison metrics are win rate, average victory points, and average rank | Already aligned with existing benchmark outputs | — Pending |
| Reproducibility gate requires clean baseline or explicit override note | Prevents misleading benchmark conclusions from local drift | — Pending |
| Commit policy is one atomic commit per planned step | Required by assignment and improves auditability | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition:**
1. Requirements invalidated? -> Move to Out of Scope with reason
2. Requirements validated? -> Move to Validated with phase reference
3. New requirements emerged? -> Add to Active
4. Decisions to log? -> Add to Key Decisions
5. "What This Is" still accurate? -> Update if drifted

**After each milestone:**
1. Full review of all sections
2. Core Value check - still the right priority?
3. Audit Out of Scope - reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-15 after initialization*