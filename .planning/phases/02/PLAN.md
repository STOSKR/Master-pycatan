# Phase 02 - Plan & Verification Design (Execution Checklist)

## Objective
Convert Phase 1 findings into executable implementation plans, full verification coverage, and commit discipline before any coding begins.

## Requirement Coverage
- PLAN-02
- PLAN-03

## Dependencies
- Phase 01 artifacts must exist:
  - `.planning/phases/01/callback-map.md`
  - `.planning/phases/01/benchmark-protocol.md`
  - `.planning/phases/01/reproducibility-schema.md`
  - `.planning/phases/01/import-path-baseline.count`

Dependency verification:
```bash
test -f .planning/phases/01/callback-map.md
test -f .planning/phases/01/benchmark-protocol.md
test -f .planning/phases/01/reproducibility-schema.md
test -f .planning/phases/01/import-path-baseline.count
```

## Scope Guardrails
- Allowed edits in this phase: `.planning/phases/02/*` only.
- Explicitly forbidden in this phase: edits to `PyCatan/**/*.py`, `benchmark_vs_random.py`, `benchmark_vs_agentes_estandar.py`.

## Mandatory Risk Gates (run at start and before each commit)

### 1) Dirty worktree gate
```bash
git status --short
```
Pass criteria:
- Either clean, or non-phase changes are recorded in `.planning/phases/02/dirty-worktree-override.md`.

### 2) Import-path consistency gate (must not regress during docs-only phase)
```bash
BASE=$(cat .planning/phases/01/import-path-baseline.count)
CUR=$(grep -RE "^(from|import)[[:space:]]+(Agents|Classes|Interfaces|Managers|TraceLoader)\\b" \
  PyCatan benchmark_vs_random.py benchmark_vs_agentes_estandar.py | wc -l | tr -d ' ')
[[ "$CUR" -eq "$BASE" ]]
```
Pass criteria:
- Baseline bare-import count is unchanged during this non-code phase.

## Atomic Tasks

### Task 02.1 - Build implementation blueprint for Part 1 and Part 2
Status: [ ]

Action:
1. Write `.planning/phases/02/implementation-blueprint.md` with:
   - Phase 3-6 execution waves.
   - Required file targets per phase.
   - Hard dependencies and expected handoff artifacts.
   - Explicit references to selected frequent hook from Phase 1.
2. Include no-code boundary note until Phase 3 kickoff.

Verification commands:
```bash
grep -n "Phase 3" .planning/phases/02/implementation-blueprint.md
grep -n "Phase 4" .planning/phases/02/implementation-blueprint.md
grep -n "Phase 5" .planning/phases/02/implementation-blueprint.md
grep -n "Phase 6" .planning/phases/02/implementation-blueprint.md
grep -n "selected_frequent_hook" .planning/phases/02/implementation-blueprint.md
```

Expected artifacts:
- `.planning/phases/02/implementation-blueprint.md`

Commit boundary:
- Commit after blueprint includes all downstream phases and dependency notes.
- Suggested message: `docs(phase-02): create implementation blueprint`

---

### Task 02.2 - Build requirement-to-verification matrix
Status: [ ]

Action:
1. Write `.planning/phases/02/verification-matrix.md` with one row per v1 requirement from `.planning/REQUIREMENTS.md`.
2. For each requirement include:
   - Verification command (automated where possible).
   - Expected artifact/evidence path.
   - Pass/fail condition.

Verification commands:
```bash
python3 - <<'PY'
import re
import pathlib
import sys
req_text = pathlib.Path('.planning/REQUIREMENTS.md').read_text(encoding='utf-8')
mat_text = pathlib.Path('.planning/phases/02/verification-matrix.md').read_text(encoding='utf-8')
req_ids = sorted(set(re.findall(r'\b[A-Z]{3,4}-\d{2}\b', req_text)))
missing = [rid for rid in req_ids if rid not in mat_text]
print('requirements:', len(req_ids))
print('missing:', missing)
sys.exit(1 if missing else 0)
PY
```

Expected artifacts:
- `.planning/phases/02/verification-matrix.md`

Commit boundary:
- Commit after script reports zero missing requirement IDs.
- Suggested message: `docs(phase-02): add full requirement verification matrix`

---

### Task 02.3 - Define commit-per-step workflow and branch strategy
Status: [ ]

Action:
1. Write `.planning/phases/02/commit-workflow.md` specifying:
   - Branch naming convention.
   - Commit message pattern per phase/task.
   - One-task-one-commit rule.
   - Mandatory pre-commit checks (dirty worktree gate + import-path gate + tests/docs checks).
2. Include rollback guidance using non-destructive git commands.

Verification commands:
```bash
grep -n "one-task-one-commit" .planning/phases/02/commit-workflow.md
grep -n "branch" .planning/phases/02/commit-workflow.md
grep -n "dirty worktree" .planning/phases/02/commit-workflow.md
grep -n "import-path" .planning/phases/02/commit-workflow.md
```

Expected artifacts:
- `.planning/phases/02/commit-workflow.md`

Commit boundary:
- Commit after commit workflow includes command-level pre-commit gates.
- Suggested message: `docs(phase-02): define commit workflow and branch policy`

---

### Task 02.4 - Produce Phase 3 ready checklist and go/no-go gate
Status: [ ]

Action:
1. Write `.planning/phases/02/phase-03-ready-checklist.md` covering:
   - Inputs required from Phase 1 and Phase 2 docs.
   - Source files to be touched in Phase 3.
   - Verification commands required before first code commit.
   - Risk notes for dirty worktree and import consistency.
2. Add final summary in `.planning/phases/02/execution-log.md` with completion timestamps.

Verification commands:
```bash
test -f .planning/phases/02/phase-03-ready-checklist.md
test -f .planning/phases/02/execution-log.md
grep -n "dirty worktree" .planning/phases/02/phase-03-ready-checklist.md
grep -n "import" .planning/phases/02/phase-03-ready-checklist.md
```

Expected artifacts:
- `.planning/phases/02/phase-03-ready-checklist.md`
- `.planning/phases/02/execution-log.md`

Commit boundary:
- Commit once go/no-go checklist is complete and all task statuses are recorded.
- Suggested message: `docs(phase-02): finalize phase-03 readiness checklist`

## Phase Exit Verification
```bash
# Should only include phase-02 planning files (or documented override)
git diff --name-only | grep -Ev '^\.planning/phases/02/'

# Import baseline must remain unchanged in docs-only phase
BASE=$(cat .planning/phases/01/import-path-baseline.count)
CUR=$(grep -RE "^(from|import)[[:space:]]+(Agents|Classes|Interfaces|Managers|TraceLoader)\\b" \
  PyCatan benchmark_vs_random.py benchmark_vs_agentes_estandar.py | wc -l | tr -d ' ')
[[ "$CUR" -eq "$BASE" ]]
```
Exit criteria:
- First command returns no lines (or override is documented).
- Import baseline count remains unchanged.
- All Task 02.1-02.4 checkboxes are complete.
