# Requirements: Master-pycatan Catan Agents Assignment

**Defined:** 2026-04-15
**Core Value:** Deliver reproducible, evidence-backed comparison of heuristic and LLM agent decisions in the same Catan engine.

## v1 Requirements

Requirements for the assignment release. Each requirement maps to exactly one roadmap phase.

### Investigation & Planning

- [ ] **STDY-01**: Callback map identifies all decision hooks and selects one frequent in-game hook for LLM control.
- [ ] **STDY-02**: Baseline benchmark protocol is defined (opponents, match counts, seeds, metrics, hardware notes).
- [ ] **STDY-03**: Reproducibility artifact schema is defined for outputs (CSV, metadata, logs).
- [ ] **PLAN-01**: Work is gated in strict order: Investigate/Study -> Plan -> Write code.
- [ ] **PLAN-02**: Verification checklist is defined for Part 1 and Part 2 before coding starts.
- [ ] **PLAN-03**: Commit-per-step policy and branch strategy are documented.

### Part 1 Heuristic Agent

- [ ] **HEUR-01**: A reusable heuristic module is implemented for placement and in-game action scoring.
- [ ] **HEUR-02**: Heuristic logic controls on_game_start and returns valid settlement/road choices.
- [ ] **HEUR-03**: Heuristic logic controls one frequent in-game callback and returns valid actions.
- [ ] **HEUR-04**: Heuristic behavior is configurable via parameters/constants without logic duplication.
- [ ] **RISK-02**: New or edited modules keep import paths consistent with canonical PyCatan package style.

### Benchmark & Reproducibility

- [ ] **BNCH-01**: Benchmark run against Random baseline is executed and exported.
- [ ] **BNCH-02**: Benchmark run against standard-agent pool is executed and exported.
- [ ] **BNCH-03**: Benchmark outputs report win rate, average victory points, and average rank.
- [ ] **BNCH-04**: Every benchmark output records reproducibility metadata (git hash, seed, command, config).
- [ ] **RISK-01**: Benchmark preflight checks dirty worktree and blocks or warns with explicit override note.

### Part 2 LLM Integration

- [ ] **LLM-01**: A provider-agnostic LLM adapter interface is implemented.
- [ ] **LLM-02**: Local Ollama model integration works through the adapter.
- [ ] **LLM-03**: AWS Bedrock model integration works through the adapter.
- [ ] **LLM-04**: UPV API model integration works through the adapter.
- [ ] **LLM-05**: At least three prompt variants exist for each required LLM decision point.
- [ ] **LLM-06**: on_game_start supports LLM decision output with schema validation and heuristic fallback.
- [ ] **LLM-07**: Selected frequent in-game callback supports LLM decision output with timeout and fallback.
- [ ] **RISK-03**: Provider errors/timeouts never crash the game loop and always fall back safely.

### Lightweight Evaluation & Delivery

- [ ] **EVAL-01**: Lightweight prompt-variant evaluation runs with a fixed match budget and exports summary results.
- [ ] **EVAL-02**: Lightweight model evaluation compares at least three models spanning Ollama, Bedrock, and UPV.
- [ ] **EVAL-03**: Qualitative logs/traces are captured for at least one representative game per setup.
- [ ] **DOC-01**: Final report/memory is produced within 10 pages and covers method, results, and limitations.
- [ ] **DOC-02**: Reproducibility appendix lists setup commands, env-var placeholders, and run commands.
- [ ] **DOC-03**: Delivery index maps final agents, scripts, outputs, and execution instructions.

## v2 Requirements

Deferred improvements after assignment scope.

### Extensions

- **V2-01**: Automated prompt optimization loop over strategy outcomes.
- **V2-02**: Larger tournament-scale benchmark orchestration with sampling controls.
- **V2-03**: Optional dashboard for comparing model/prompt runs interactively.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Training or fine-tuning custom LLMs | Not required for assignment grading |
| Full MLOps deployment pipeline | Repo is local simulation workflow |
| Visualizer UI overhaul | Not needed for core assignment outcomes |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| STDY-01 | Phase 1 | Pending |
| STDY-02 | Phase 1 | Pending |
| STDY-03 | Phase 1 | Pending |
| PLAN-01 | Phase 1 | Pending |
| PLAN-02 | Phase 2 | Pending |
| PLAN-03 | Phase 2 | Pending |
| HEUR-01 | Phase 3 | Pending |
| HEUR-02 | Phase 3 | Pending |
| HEUR-03 | Phase 3 | Pending |
| HEUR-04 | Phase 3 | Pending |
| RISK-02 | Phase 3 | Pending |
| BNCH-01 | Phase 4 | Pending |
| BNCH-02 | Phase 4 | Pending |
| BNCH-03 | Phase 4 | Pending |
| BNCH-04 | Phase 4 | Pending |
| RISK-01 | Phase 4 | Pending |
| LLM-01 | Phase 5 | Pending |
| LLM-02 | Phase 5 | Pending |
| LLM-03 | Phase 5 | Pending |
| LLM-04 | Phase 5 | Pending |
| LLM-05 | Phase 5 | Pending |
| LLM-06 | Phase 5 | Pending |
| LLM-07 | Phase 5 | Pending |
| RISK-03 | Phase 5 | Pending |
| EVAL-01 | Phase 6 | Pending |
| EVAL-02 | Phase 6 | Pending |
| EVAL-03 | Phase 6 | Pending |
| DOC-01 | Phase 6 | Pending |
| DOC-02 | Phase 6 | Pending |
| DOC-03 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-15*
*Last updated: 2026-04-15 after roadmap initialization*