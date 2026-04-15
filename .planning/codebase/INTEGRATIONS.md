# External Integrations

**Analysis Date:** 2026-04-15

## APIs & External Services

**Web UI/CDN:**
- Bootstrap CDN - visualizer layout and components (`PyCatan/Visualizer/index.html`).
  - SDK/Client: browser `<link>/<script>` includes.
  - Auth: Not applicable.
- jQuery CDN - visualizer DOM/event handling (`PyCatan/Visualizer/index.html`, `PyCatan/Visualizer/JS/general.js`).
  - SDK/Client: browser `<script>` include.
  - Auth: Not applicable.
- Animate.css, GSAP, canvas-confetti, Font Awesome CDNs - visual effects/icons in visualizer.
  - SDK/Client: browser `<script>/<link>` includes.
  - Auth: Not applicable.

**Simulation APIs:**
- Not detected (no HTTP client/server code in core Python modules).

## Data Storage

**Databases:**
- Not detected.
  - Connection: Not applicable.
  - Client: Not applicable.

**File Storage:**
- Local filesystem for game traces (`PyCatan/TraceLoader/TraceLoader.py`).
- Trace fixtures committed for regression checks (`PyCatan/Tests/test_traces/game_*.json`, 100 files detected).
- Benchmark outputs written to CSV in repo root (`benchmark_vs_random.py`, `benchmark_vs_agentes_estandar.py`).

**Caching:**
- None detected.

## Authentication & Identity

**Auth Provider:**
- Custom auth not applicable (single-process local simulator).
  - Implementation: Not applicable.

## Monitoring & Observability

**Error Tracking:**
- None detected.

**Logs:**
- Console printing and traceback output (`benchmark_vs_random.py`, `benchmark_vs_agentes_estandar.py`, `PyCatan/Managers/GameManager.py`).

## CI/CD & Deployment

**Hosting:**
- Not detected.

**CI Pipeline:**
- Not detected (`.github/workflows` not present in scanned tree).

## Environment Configuration

**Required env vars:**
- Not detected in source.

**Secrets location:**
- `.env` exists at repository root (contents intentionally not inspected).

## Webhooks & Callbacks

**Incoming:**
- None.

**Outgoing:**
- None.

---

*Integration audit: 2026-04-15*
