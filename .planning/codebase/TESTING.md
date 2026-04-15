# Testing Patterns

**Analysis Date:** 2026-04-15

## Test Framework

**Runner:**
- pytest-style test discovery (files named `test_*.py`, classes `Test*`, methods `test_*`).
- Config: Not detected (`pytest.ini`, `pyproject.toml`, and `setup.cfg` are absent).

**Assertion Library:**
- Native `assert` statements.

**Run Commands:**
```bash
python3 -m pip install pytest         # Required first in this environment
python3 -m pytest -q PyCatan/Tests    # Run all tests
python3 -m pytest -q PyCatan/Tests/test_game_manager.py
```

## Test File Organization

**Location:**
- Centralized under `PyCatan/Tests/`.

**Naming:**
- `test_<domain>.py` (for example `test_board.py`, `test_materials.py`).

**Structure:**
```
PyCatan/Tests/
|- test_*.py
\- test_traces/game_*.json
```

## Test Structure

**Suite Organization:**
```python
class TestGameManager:
    game_manager = GameManager(for_test='test_específico')

    def test_build_city(self):
        self.game_manager.reset_game_values()
        assert self.game_manager.build_city(0, 0)['response'] is False
```

**Patterns:**
- Setup pattern: direct object construction + explicit state mutation.
- Teardown pattern: no dedicated teardown; many tests call `reset_game_values()`.
- Assertion pattern: direct equality/boolean checks on dict fields and object state.

## Mocking

**Framework:**
- Not used.

**Patterns:**
```python
# Deterministic behavior typically uses fixed board state and direct mutation,
# not mocks or monkeypatching.
board.nodes[0]['player'] = 0
assert board.build_road(0, 0, 1)['response'] is True
```

**What to Mock:**
- External boundaries are minimal; if adding I/O/network later, isolate with adapters before mocking.

**What NOT to Mock:**
- Core game rules in `Board`/`GameManager`; tests currently exercise real logic directly.

## Fixtures and Factories

**Test Data:**
```python
trade = TradeOffer(Materials(1, 0, 0, 0, 0), Materials(0, 0, 1, 0, 1))
answer_object = game_manager.send_trade_to_everyone(trade)
assert len(answer_object) == 3
```

**Location:**
- Large JSON fixtures in `PyCatan/Tests/test_traces/` (100 files).

## Coverage

**Requirements:**
- None enforced (no coverage threshold/config detected).

**View Coverage:**
```bash
python3 -m pytest --cov=PyCatan PyCatan/Tests
```

## Test Types

**Unit Tests:**
- Strong coverage for `Classes/*` and manager methods via direct state assertions.

**Integration Tests:**
- `test_trace_comparison.py` replays games and compares generated traces against fixture JSONs.

**E2E Tests:**
- Not used.

## Common Patterns

**Async Testing:**
```python
# Not applicable: repository logic is synchronous.
```

**Error Testing:**
```python
# Invalid operations are validated via response flags.
assert board.build_town(2, 0)['response'] is False
```

---

*Testing analysis: 2026-04-15*
