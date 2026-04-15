# Roadmap: Master-pycatan Catan Agents Assignment

## Overview

This roadmap delivers the assignment in strict gated order: investigate current engine behavior and reproducibility constraints first, lock the implementation plan second, then execute Part 1 (heuristic agent + benchmark evidence) and Part 2 (LLM integration + lightweight evaluation) with final reporting artifacts.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [ ] **Phase 1: Investigate & Baseline Study** - Lock decision hooks, reproducibility protocol, and gating rules before coding.
- [ ] **Phase 2: Plan & Verification Design** - Finalize execution checklist, commit discipline, and phase-ready verification criteria.
- [ ] **Phase 3: Part 1 Heuristic Agent Implementation** - Build reusable heuristic decisions for required callbacks with import consistency.
- [ ] **Phase 4: Part 1 Benchmark & Reproducibility Evidence** - Run benchmark suite and capture reproducible result artifacts.
- [ ] **Phase 5: Part 2 LLM Integration** - Add multi-provider model adapters, prompt variants, and safe runtime fallbacks.
- [ ] **Phase 6: Lightweight LLM Evaluation & Assignment Delivery** - Produce lightweight comparisons and complete report/delivery bundle.

## Phase Details

### Phase 1: Investigate & Baseline Study
**Goal**: Establish verified understanding of engine hooks and a reproducible baseline protocol before any implementation.
**Depends on**: Nothing (first phase)
**Requirements**: STDY-01, STDY-02, STDY-03, PLAN-01
**Success Criteria** (what must be TRUE):
  1. Callback decision map is documented and one frequent in-game LLM hook is selected.
  2. Baseline benchmark protocol is defined with explicit opponents, metrics, and run budget.
  3. Reproducibility artifact schema is defined (CSV, metadata, logs) and ready for use.
  4. Investigate -> Plan -> Write stage gate is explicitly documented and accepted.
**Verification**:
- [ ] Decision-hook selection document exists and names required callbacks.
- [ ] Baseline protocol checklist is complete and versioned.
- [ ] Reproducibility schema template is committed.
**Plans**: 4 plans

Plans:
- [ ] 01-01: Map AgentInterface callbacks and select frequent decision hook
- [ ] 01-02: Define benchmark protocol and run-budget assumptions
- [ ] 01-03: Define reproducibility artifact structure and metadata fields
- [ ] 01-04: Finalize stage-gate criteria for Investigate complete

### Phase 2: Plan & Verification Design
**Goal**: Convert study outcomes into executable implementation plans with explicit verification and commit policy.
**Depends on**: Phase 1
**Requirements**: PLAN-02, PLAN-03
**Success Criteria** (what must be TRUE):
  1. Part 1 and Part 2 verification checklists are complete before coding starts.
  2. Commit-per-step strategy is defined with atomic scope boundaries.
  3. Plan artifacts clearly separate investigation, planning, and coding waves.
**Verification**:
- [ ] Verification matrix covers all v1 requirements.
- [ ] Commit strategy and branch conventions are documented.
- [ ] First coding phase has approved plan checklist.
**Plans**: 3 plans

Plans:
- [ ] 02-01: Draft implementation blueprint for Part 1 and Part 2
- [ ] 02-02: Build requirement-to-test verification matrix
- [ ] 02-03: Define commit-per-step workflow and handoff rules

### Phase 3: Part 1 Heuristic Agent Implementation
**Goal**: Implement clean, reusable heuristic logic for required callbacks while preserving engine compatibility.
**Depends on**: Phase 2
**Requirements**: HEUR-01, HEUR-02, HEUR-03, HEUR-04, RISK-02
**Success Criteria** (what must be TRUE):
  1. Heuristic agent can complete games without breaking AgentInterface expectations.
  2. on_game_start uses explicit heuristic scoring to output valid settlement and road choices.
  3. Selected frequent callback uses explicit heuristic scoring to output valid actions.
  4. Heuristic logic is reusable/configurable and imports follow canonical PyCatan package style.
**Verification**:
- [ ] Smoke game run completes with heuristic agent in all positions.
- [ ] Callback outputs validate against legal action expectations.
- [ ] Import checks confirm no new mixed bare import-path usage.
**Plans**: 4 plans

Plans:
- [ ] 03-01: Implement reusable heuristic scoring module
- [ ] 03-02: Integrate heuristic on_game_start decision logic
- [ ] 03-03: Integrate heuristic frequent in-game decision logic
- [ ] 03-04: Add compatibility checks and import-path consistency checks

### Phase 4: Part 1 Benchmark & Reproducibility Evidence
**Goal**: Produce reproducible Part 1 benchmark evidence against required baselines.
**Depends on**: Phase 3
**Requirements**: BNCH-01, BNCH-02, BNCH-03, BNCH-04, RISK-01
**Success Criteria** (what must be TRUE):
  1. Heuristic vs Random and heuristic vs standard benchmarks both run and export results.
  2. Reported metrics include win rate, average victory points, and average rank.
  3. Each benchmark artifact includes command, seed, git hash, and agent configuration metadata.
  4. Benchmark preflight catches dirty worktree conditions before final runs.
**Verification**:
- [ ] Two benchmark result sets exist (random and standard pools).
- [ ] Metrics table is generated from exported outputs.
- [ ] Metadata fields are present and reproducible rerun command works.
**Plans**: 4 plans

Plans:
- [ ] 04-01: Add benchmark preflight and metadata capture
- [ ] 04-02: Execute heuristic vs random benchmark scenario
- [ ] 04-03: Execute heuristic vs standard-agent benchmark scenario
- [ ] 04-04: Summarize Part 1 results and reproducibility package

### Phase 5: Part 2 LLM Integration
**Goal**: Integrate multi-provider LLM decisioning for required callbacks with robust safety fallbacks.
**Depends on**: Phase 4
**Requirements**: LLM-01, LLM-02, LLM-03, LLM-04, LLM-05, LLM-06, LLM-07, RISK-03
**Success Criteria** (what must be TRUE):
  1. Provider-agnostic adapter can invoke Ollama, AWS Bedrock, and UPV API models.
  2. At least three prompt variants are available for each required decision point.
  3. on_game_start and selected frequent callback both support LLM outputs with schema validation.
  4. Timeout/provider failures always trigger safe fallback and games continue without crashes.
  5. At least three model configurations can be switched without code edits.
**Verification**:
- [ ] Provider connectivity smoke tests pass for all three backends.
- [ ] Prompt variant switching is validated by configuration-only changes.
- [ ] Failure injection confirms fallback behavior keeps match execution stable.
**Plans**: 6 plans

Plans:
- [ ] 05-01: Implement provider-agnostic adapter interface and config wiring
- [ ] 05-02: Integrate Ollama adapter and model configuration
- [ ] 05-03: Integrate AWS Bedrock adapter and model configuration
- [ ] 05-04: Integrate UPV API adapter and model configuration
- [ ] 05-05: Implement prompt-variant framework (>=3 variants)
- [ ] 05-06: Integrate LLM decisions for required callbacks with safety fallbacks

### Phase 6: Lightweight LLM Evaluation & Assignment Delivery
**Goal**: Produce lightweight prompt/model evidence and final assignment deliverables.
**Depends on**: Phase 5
**Requirements**: EVAL-01, EVAL-02, EVAL-03, DOC-01, DOC-02, DOC-03
**Success Criteria** (what must be TRUE):
  1. Lightweight prompt-variant and model-comparison evaluations run with fixed budgets.
  2. Evaluation outputs include quantitative summaries and representative qualitative logs/traces.
  3. Final report/memory stays within 10 pages and documents method, results, and limitations.
  4. Delivery index clearly maps final code, scripts, outputs, and rerun commands.
**Verification**:
- [ ] Prompt and model evaluation summary files are generated.
- [ ] Qualitative trace/log samples are attached for representative runs.
- [ ] Final report and delivery index pass checklist review.
**Plans**: 5 plans

Plans:
- [ ] 06-01: Run lightweight prompt-variant evaluation
- [ ] 06-02: Run lightweight model comparison across Ollama/Bedrock/UPV
- [ ] 06-03: Capture representative qualitative logs/traces
- [ ] 06-04: Produce final report (<=10 pages) and reproducibility appendix
- [ ] 06-05: Build final delivery index and submission bundle

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Investigate & Baseline Study | 0/4 | Not started | - |
| 2. Plan & Verification Design | 0/3 | Not started | - |
| 3. Part 1 Heuristic Agent Implementation | 0/4 | Not started | - |
| 4. Part 1 Benchmark & Reproducibility Evidence | 0/4 | Not started | - |
| 5. Part 2 LLM Integration | 0/6 | Not started | - |
| 6. Lightweight LLM Evaluation & Assignment Delivery | 0/5 | Not started | - |