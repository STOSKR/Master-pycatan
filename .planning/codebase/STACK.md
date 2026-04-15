# Technology Stack

**Analysis Date:** 2026-04-15

## Languages

**Primary:**
- Python 3.x - Core game engine, agents, benchmarks, and tests (`PyCatan/**/*.py`, `benchmark_vs_random.py`, `benchmark_vs_agentes_estandar.py`).

**Secondary:**
- JavaScript/HTML/CSS - Trace visualizer (`PyCatan/Visualizer/index.html`, `PyCatan/Visualizer/JS/general.js`, `PyCatan/Visualizer/CSS/*.css`).

## Runtime

**Environment:**
- CPython 3.x (README states Python 3.x; local environment observed as `Python 3.12.3`).

**Package Manager:**
- pip (implied by Python workflow).
- Lockfile: missing.

## Frameworks

**Core:**
- Custom object-oriented simulation engine - game orchestration and rules (`PyCatan/Managers/GameDirector.py`, `PyCatan/Managers/GameManager.py`).

**Testing:**
- Pytest-style test suite (test naming/classes/assert style in `PyCatan/Tests/*.py`), but no test config file detected and `pytest` not installed in current environment.

**Build/Dev:**
- No formal build system detected.
- Parallel execution via standard library `concurrent.futures.ProcessPoolExecutor` (`benchmark_vs_random.py`, `benchmark_vs_agentes_estandar.py`).

## Key Dependencies

**Critical:**
- Python standard library modules (`random`, `copy`, `math`, `importlib`, `concurrent.futures`, `json`, `pathlib`) power simulation and benchmark orchestration.

**Infrastructure:**
- Browser CDN dependencies for visualizer UI: Bootstrap, jQuery, Popper, Animate.css, GSAP, canvas-confetti, Font Awesome (`PyCatan/Visualizer/index.html`).

## Configuration

**Environment:**
- `.env` file present at repo root; `.gitignore` currently only ignores `.env`.
- No in-repo parser/loader for env vars detected in Python source.

**Build:**
- Build/test config files such as `pyproject.toml`, `requirements.txt`, `pytest.ini`, `setup.cfg`, and CI workflow files are not detected.

## Platform Requirements

**Development:**
- Python 3.x runtime.
- Working directory and import path must be chosen carefully because the repo mixes `from PyCatan...` and bare `from Agents/Classes/Managers...` imports.

**Production:**
- Local/offline script execution model (no deployment target or service runtime detected).

---

*Stack analysis: 2026-04-15*
