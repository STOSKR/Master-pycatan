# Phase 03 - Part 1 Heuristic Implementation (Execution Checklist)

## Objective
Implement a reusable heuristic agent for required callbacks (`on_game_start` and selected frequent hook) with compatibility checks and import-path consistency controls.

## Requirement Coverage
- HEUR-01
- HEUR-02
- HEUR-03
- HEUR-04
- RISK-02

## Dependencies
- `.planning/phases/02/phase-03-ready-checklist.md` approved.
- `.planning/phases/01/import-path-baseline.count` available for regression checks.

Dependency verification:
```bash
test -f .planning/phases/02/phase-03-ready-checklist.md
test -f .planning/phases/01/import-path-baseline.count
```

## Mandatory Risk Gates (run at start and before each commit)

### 1) Dirty worktree gate (code phase)
```bash
git status --short
```
Pass criteria:
- Prefer clean tree before coding.
- If unrelated local changes are intentionally kept, record them in `.planning/phases/03/dirty-worktree-override.md` (with date, files, reason) and continue only with explicit note.

### 2) Import-path consistency gate
```bash
BASE=$(cat .planning/phases/01/import-path-baseline.count)
CUR=$(grep -RE "^(from|import)[[:space:]]+(Agents|Classes|Interfaces|Managers|TraceLoader)\\b" \
  PyCatan benchmark_vs_random.py benchmark_vs_agentes_estandar.py | wc -l | tr -d ' ')
[[ "$CUR" -le "$BASE" ]]
```
Pass criteria:
- Bare-import count does not increase.

### 3) Changed-file canonical import gate
```bash
CHANGED=$(git diff --name-only -- '*.py')
if [[ -n "$CHANGED" ]]; then
  if grep -En "^(from|import)[[:space:]]+(Agents|Classes|Interfaces|Managers|TraceLoader)\\b" $CHANGED; then
    echo "FAIL: changed Python files contain bare imports"
    exit 1
  fi
fi
```
Pass criteria:
- No newly edited Python file introduces bare top-level imports.

## Planned File Targets
- `PyCatan/Agents/HeuristicScoring.py`
- `PyCatan/Agents/HeuristicAgent.py`
- `PyCatan/Tests/test_heuristic_scoring.py`
- `PyCatan/Tests/test_heuristic_game_start.py`
- `PyCatan/Tests/test_heuristic_build_phase.py`
- `.planning/phases/03/execution-log.md`

## Atomic Tasks

### Task 03.1 - Create heuristic scoring core and config knobs
Status: [ ]

Action:
1. Add `PyCatan/Agents/HeuristicScoring.py` with reusable scoring functions for:
   - Initial settlement scoring.
   - Initial road-choice scoring.
   - Build-phase action scoring.
2. Add configurable weights/constants (single config object/module, no duplicated constants in agent methods).
3. Add `PyCatan/Tests/test_heuristic_scoring.py` covering deterministic scoring and tie-break behavior.

Verification commands:
```bash
python3 -m pytest -q PyCatan/Tests/test_heuristic_scoring.py
python3 -m py_compile PyCatan/Agents/HeuristicScoring.py
```

Expected artifacts:
- `PyCatan/Agents/HeuristicScoring.py`
- `PyCatan/Tests/test_heuristic_scoring.py`

Commit boundary:
- Commit after scoring module and tests pass.
- Suggested message: `feat(phase-03): add reusable heuristic scoring core`

---

### Task 03.2 - Implement heuristic on_game_start behavior
Status: [ ]

Action:
1. Add `PyCatan/Agents/HeuristicAgent.py` extending `AgentInterface`.
2. Implement `on_game_start` using scoring module to choose valid node and adjacent road.
3. Ensure output format matches engine expectation `(node_id, road_to)`.
4. Add `PyCatan/Tests/test_heuristic_game_start.py` validating legal output against board constraints.

Verification commands:
```bash
python3 -m pytest -q PyCatan/Tests/test_heuristic_game_start.py
python3 -m py_compile PyCatan/Agents/HeuristicAgent.py
```

Expected artifacts:
- `PyCatan/Agents/HeuristicAgent.py`
- `PyCatan/Tests/test_heuristic_game_start.py`

Commit boundary:
- Commit after game-start tests pass and import gates pass.
- Suggested message: `feat(phase-03): integrate heuristic on_game_start decision`

---

### Task 03.3 - Implement heuristic frequent callback behavior (default on_build_phase)
Status: [ ]

Action:
1. Implement `on_build_phase` in `HeuristicAgent` using reusable scoring/config (no duplicated logic from Task 03.1).
2. Ensure returned action dict follows expected schema from existing agents/game manager.
3. Add `PyCatan/Tests/test_heuristic_build_phase.py` with valid-action and no-action edge cases.

Verification commands:
```bash
python3 -m pytest -q PyCatan/Tests/test_heuristic_build_phase.py
python3 -m pytest -q PyCatan/Tests/test_heuristic_game_start.py PyCatan/Tests/test_heuristic_scoring.py
```

Expected artifacts:
- Updated `PyCatan/Agents/HeuristicAgent.py`
- `PyCatan/Tests/test_heuristic_build_phase.py`

Commit boundary:
- Commit after build-phase tests and changed-file import gate pass.
- Suggested message: `feat(phase-03): integrate heuristic on_build_phase logic`

---

### Task 03.4 - Compatibility smoke checks and regression safety
Status: [ ]

Action:
1. Run targeted existing regression tests that touch core flow:
   - `PyCatan/Tests/test_game_manager.py`
   - `PyCatan/Tests/test_game_director.py`
2. Run a lightweight smoke simulation using `GameDirector` with `HeuristicAgent` + baseline opponents (single game, no trace storage).
3. Record results and command outputs in `.planning/phases/03/execution-log.md`.

Verification commands:
```bash
python3 -m pytest -q PyCatan/Tests/test_game_manager.py PyCatan/Tests/test_game_director.py
python3 - <<'PY'
from PyCatan.Agents.HeuristicAgent import HeuristicAgent
from PyCatan.Agents.RandomAgent import RandomAgent
from PyCatan.Managers.GameDirector import GameDirector
agents = [HeuristicAgent, RandomAgent, RandomAgent, RandomAgent]
gd = GameDirector(agents=agents, max_rounds=80, store_trace=False)
trace = gd.game_start(print_outcome=False)
assert 'game' in trace and trace['game'], 'Smoke game produced empty trace'
print('smoke_ok')
PY
```

Expected artifacts:
- `.planning/phases/03/execution-log.md`

Commit boundary:
- Commit after smoke run and regression tests pass.
- Suggested message: `test(phase-03): add heuristic compatibility smoke evidence`

---

### Task 03.5 - Final import consistency audit for touched files
Status: [ ]

Action:
1. Audit all newly created/edited Python files in this phase for canonical imports (`from PyCatan...`).
2. Append import-audit summary to `.planning/phases/03/execution-log.md` with:
   - files checked
   - command output
   - pass/fail
3. If any violation exists, fix before phase close.

Verification commands:
```bash
CHANGED=$(git diff --name-only -- '*.py')
if [[ -n "$CHANGED" ]]; then
  ! grep -En "^(from|import)[[:space:]]+(Agents|Classes|Interfaces|Managers|TraceLoader)\\b" $CHANGED
fi
```

Expected artifacts:
- Updated `.planning/phases/03/execution-log.md`

Commit boundary:
- Commit after audit passes and log is updated.
- Suggested message: `chore(phase-03): enforce import-path consistency audit`

## Phase Exit Verification
```bash
python3 -m pytest -q \
  PyCatan/Tests/test_heuristic_scoring.py \
  PyCatan/Tests/test_heuristic_game_start.py \
  PyCatan/Tests/test_heuristic_build_phase.py \
  PyCatan/Tests/test_game_manager.py \
  PyCatan/Tests/test_game_director.py

BASE=$(cat .planning/phases/01/import-path-baseline.count)
CUR=$(grep -RE "^(from|import)[[:space:]]+(Agents|Classes|Interfaces|Managers|TraceLoader)\\b" \
  PyCatan benchmark_vs_random.py benchmark_vs_agentes_estandar.py | wc -l | tr -d ' ')
[[ "$CUR" -le "$BASE" ]]
```
Exit criteria:
- All phase tests above pass.
- Import-path baseline does not regress.
- Task 03.1-03.5 are complete with one commit per task.
