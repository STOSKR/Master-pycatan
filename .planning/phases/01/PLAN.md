# Phase 01 - Investigate & Baseline Study (Execution Checklist)

## Objective
Establish callback decisions, baseline benchmark protocol, reproducibility schema, and explicit stage gates before any source-code implementation.

## Requirement Coverage
- STDY-01
- STDY-02
- STDY-03
- PLAN-01

## Scope Guardrails
- Allowed edits in this phase: `.planning/phases/01/*` only.
- Explicitly forbidden in this phase: edits to `PyCatan/**/*.py`, `benchmark_vs_random.py`, `benchmark_vs_agentes_estandar.py`.

## Mandatory Risk Gates (run at start and before each commit)

### 1) Dirty worktree gate
```bash
git status --short
```
Pass criteria:
- Either output is empty, or
- Any non-phase files are documented in `.planning/phases/01/dirty-worktree-override.md` with justification, date, and exact file list.

### 2) Import-path consistency baseline gate
```bash
grep -REn "^(from|import)[[:space:]]+(Agents|Classes|Interfaces|Managers|TraceLoader)\\b" \
  PyCatan benchmark_vs_random.py benchmark_vs_agentes_estandar.py \
  | tee .planning/phases/01/import-path-baseline.txt

grep -RE "^(from|import)[[:space:]]+(Agents|Classes|Interfaces|Managers|TraceLoader)\\b" \
  PyCatan benchmark_vs_random.py benchmark_vs_agentes_estandar.py \
  | wc -l | tr -d ' ' > .planning/phases/01/import-path-baseline.count
```
Pass criteria:
- `.planning/phases/01/import-path-baseline.txt` exists.
- `.planning/phases/01/import-path-baseline.count` exists and contains an integer.

## Atomic Tasks

### Task 01.1 - Preflight snapshot and risk record
Status: [ ]

Action:
1. Create `.planning/phases/01/execution-log.md` with date, operator, branch, and intent.
2. Run both mandatory risk gates.
3. If worktree is dirty beyond phase docs, create `.planning/phases/01/dirty-worktree-override.md`.

Verification commands:
```bash
test -f .planning/phases/01/execution-log.md
test -f .planning/phases/01/import-path-baseline.txt
test -f .planning/phases/01/import-path-baseline.count
```

Expected artifacts:
- `.planning/phases/01/execution-log.md`
- `.planning/phases/01/import-path-baseline.txt`
- `.planning/phases/01/import-path-baseline.count`
- `.planning/phases/01/dirty-worktree-override.md` (conditional)

Commit boundary:
- Commit after only Task 01.1 artifacts are staged.
- Suggested message: `docs(phase-01): capture preflight risk baseline`

---

### Task 01.2 - Callback map and frequent hook decision
Status: [ ]

Action:
1. Inspect callback contract and call sites:
   - `PyCatan/Interfaces/AgentInterface.py`
   - `PyCatan/Managers/GameDirector.py`
   - `PyCatan/Managers/GameManager.py`
2. Write `.planning/phases/01/callback-map.md` with:
   - Full callback inventory (`on_*`).
   - Call frequency estimate (startup/turn-loop/rare card triggers).
   - Selected frequent hook (expected default: `on_build_phase`) and rationale.
   - Impact/risk notes for Part 2 LLM hooking.

Verification commands:
```bash
grep -n "selected_frequent_hook:" .planning/phases/01/callback-map.md
grep -n "on_game_start" .planning/phases/01/callback-map.md
grep -n "on_build_phase" .planning/phases/01/callback-map.md
```

Expected artifacts:
- `.planning/phases/01/callback-map.md`

Commit boundary:
- Commit after callback map is complete and reviewed against interface methods.
- Suggested message: `docs(phase-01): map callbacks and lock frequent hook`

---

### Task 01.3 - Baseline benchmark protocol definition
Status: [ ]

Action:
1. Review current benchmark scripts:
   - `benchmark_vs_random.py`
   - `benchmark_vs_agentes_estandar.py`
2. Write `.planning/phases/01/benchmark-protocol.md` including:
   - Opponent sets (random and standard pool).
   - Run budget (matches/position, max rounds, worker ratio assumptions).
   - Required metrics (`win_rate`, `avg_victory_points`, `avg_rank`).
   - Seed policy and hardware metadata policy.
   - Acceptance criteria for reproducible reruns.

Verification commands:
```bash
grep -n "win_rate" .planning/phases/01/benchmark-protocol.md
grep -n "avg_victory_points" .planning/phases/01/benchmark-protocol.md
grep -n "avg_rank" .planning/phases/01/benchmark-protocol.md
grep -n "seed" .planning/phases/01/benchmark-protocol.md
```

Expected artifacts:
- `.planning/phases/01/benchmark-protocol.md`

Commit boundary:
- Commit once protocol includes all required metric and reproducibility fields.
- Suggested message: `docs(phase-01): define benchmark protocol and run budget`

---

### Task 01.4 - Reproducibility artifact schema and template
Status: [ ]

Action:
1. Write `.planning/phases/01/reproducibility-schema.md` describing required outputs:
   - CSV results
   - Metadata JSON
   - Optional trace/log references
2. Create `.planning/phases/01/reproducibility-metadata.template.json` with required keys:
   - `git_commit`
   - `command`
   - `seed`
   - `agent_config`
   - `python_version`
   - `timestamp_utc`
   - `host_info`

Verification commands:
```bash
python3 -m json.tool .planning/phases/01/reproducibility-metadata.template.json > /dev/null
grep -n "git_commit" .planning/phases/01/reproducibility-schema.md
grep -n "command" .planning/phases/01/reproducibility-schema.md
grep -n "seed" .planning/phases/01/reproducibility-schema.md
```

Expected artifacts:
- `.planning/phases/01/reproducibility-schema.md`
- `.planning/phases/01/reproducibility-metadata.template.json`

Commit boundary:
- Commit once JSON template validates and schema doc references all required metadata fields.
- Suggested message: `docs(phase-01): add reproducibility schema and metadata template`

---

### Task 01.5 - Stage gate definition (Investigate -> Plan -> Write)
Status: [ ]

Action:
1. Write `.planning/phases/01/stage-gate.md` with explicit go/no-go checks:
   - Investigate complete criteria.
   - Required artifacts for entering Phase 2.
   - Prohibition on source-code edits until Phase 2 completion.
2. Add final checklist in `.planning/phases/01/execution-log.md` marking Task 01.1-01.5 status.

Verification commands:
```bash
grep -n "Investigate -> Plan -> Write" .planning/phases/01/stage-gate.md
grep -n "no source-code edits" .planning/phases/01/stage-gate.md
grep -n "Task 01.5" .planning/phases/01/execution-log.md
```

Expected artifacts:
- `.planning/phases/01/stage-gate.md`
- Updated `.planning/phases/01/execution-log.md`

Commit boundary:
- Commit after stage-gate doc is complete and Task 01 checklist is updated.
- Suggested message: `docs(phase-01): finalize investigate stage gates`

## Phase Exit Verification
```bash
# Confirm only phase planning docs changed for this phase checkpoint
git diff --name-only | grep -Ev '^\.planning/phases/01/'

# Confirm risk baseline files are present
test -f .planning/phases/01/import-path-baseline.txt
test -f .planning/phases/01/import-path-baseline.count
```
Exit criteria:
- First command returns no lines (or documented override exists).
- All Task 01.1-01.5 checkboxes are complete.
