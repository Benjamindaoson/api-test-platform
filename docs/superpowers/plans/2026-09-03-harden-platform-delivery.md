# Platform Delivery Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the API management platform reproducibly buildable, database-connected, and end-to-end verifiable locally and in GitHub Actions.

**Architecture:** Compose runs a bounded `platform` profile containing PostgreSQL, Redis, FastAPI, and the Next.js UI; LangGraph stays opt-in because P0 must not require model credentials. A host-side Python smoke runner drives only public FastAPI endpoints against disposable Docker state, while CI separately verifies backend, UI, and Compose E2E contracts.

**Tech Stack:** Python 3.13, uv, FastAPI, asyncpg, PostgreSQL 16, Redis 7, Docker Compose, Node 22, Corepack pnpm 10.5.1, Next.js 15, GitHub Actions.

**Spec:** `openspec/changes/harden-platform-delivery/`

## Global Constraints

- Python images use `python:3.13-slim` to match `pyproject.toml`.
- Frontend installation always uses `pnpm install --frozen-lockfile`.
- P0 must not need model credentials or call a real RAG target.
- The smoke test creates only disposable project/test-run rows in Compose PostgreSQL.
- Every new behavioral module receives a test before implementation.

---

### Task 1: Delivery contract tests and fixtures

**Files:**
- Create: `tests/test_delivery_contract.py`
- Create: `tests/fixtures/e2e_openapi.yaml`
- Create: `tests/fixtures/e2e_generated_test.py`
- Test: `tests/test_delivery_contract.py`

**Interfaces:**
- Produces a fixture OpenAPI file containing `GET /ping` and a passing pytest target.
- Defines delivery assertions consumed by Docker/Compose implementation tasks.

- [ ] **Step 1: Write the failing contract tests**

```python
def test_ui_image_has_a_locked_pnpm_build_contract():
    dockerfile = Path("ui/Dockerfile").read_text(encoding="utf-8")
    assert "pnpm install --frozen-lockfile" in dockerfile
    assert "pnpm build" in dockerfile

def test_compose_platform_profile_has_api_healthcheck_and_ui_service():
    compose = Path("docker-compose.yml").read_text(encoding="utf-8")
    assert "platform" in compose
    assert "healthcheck:" in compose
```

- [ ] **Step 2: Run the contract tests and verify they fail because `ui/Dockerfile` is missing.**

Run: `uv run python -m pytest tests/test_delivery_contract.py -q`

- [ ] **Step 3: Add the delivery files and fixture inputs.**

- [ ] **Step 4: Run the delivery contract tests and verify they pass.**

Run: `uv run python -m pytest tests/test_delivery_contract.py -q`

### Task 2: Docker images and Compose platform profile

**Files:**
- Create: `ui/Dockerfile`
- Modify: `Dockerfile.api`
- Modify: `Dockerfile.langgraph`
- Modify: `docker-compose.yml`
- Test: `tests/test_delivery_contract.py`

**Interfaces:**
- `api` publishes `8100`, reports health after PostgreSQL connection, and depends on PostgreSQL health.
- `ui` publishes `3000` and depends on API health.
- `langgraph` is opt-in through `agent` profile.

- [ ] **Step 1: Write/extend failing tests for profile, health, and pinned image contracts.**
- [ ] **Step 2: Run them and confirm the missing profile/image failure.**
- [ ] **Step 3: Implement minimal Docker/Compose changes.**
- [ ] **Step 4: Run `docker compose config --quiet` and contract tests.**

### Task 3: Public HTTP E2E smoke runner

**Files:**
- Create: `scripts/e2e_smoke.py`
- Create: `tests/test_e2e_smoke.py`
- Test: `tests/test_e2e_smoke.py`

**Interfaces:**
- `run_smoke(base_url: str, timeout_seconds: float) -> dict[str, object]` waits for healthy database API, creates one project, synchronizes the fixture OpenAPI, runs the fixture pytest path, retrieves the persisted run, and returns IDs/counts.
- Raises `SmokeFailure` with endpoint/status context when an assertion fails.

- [ ] **Step 1: Write failing unit tests using an injected JSON request function.**
- [ ] **Step 2: Run them and verify failure because the module is absent.**
- [ ] **Step 3: Implement retrying HTTP calls and ordered assertions.**
- [ ] **Step 4: Run the unit tests and full Python suite.**

### Task 4: CI and documentation

**Files:**
- Create: `.github/workflows/platform-delivery.yml`
- Modify: `README.md`
- Modify: `openspec/changes/harden-platform-delivery/tasks.md`

**Interfaces:**
- CI executes backend tests, locked UI build, and `docker compose --profile platform up --build --wait` followed by `scripts/e2e_smoke.py`.
- README gives a verified P0 run command and states that LangGraph/real RAG are outside this smoke profile.

- [ ] **Step 1: Write a failing static contract test that requires the delivery workflow.**
- [ ] **Step 2: Run it and confirm it fails.**
- [ ] **Step 3: Add workflow and documentation.**
- [ ] **Step 4: Run contract tests, OpenSpec strict validation, and inspect workflow syntax.**

### Task 5: Integrated verification and delivery

**Files:**
- Modify: `openspec/changes/harden-platform-delivery/tasks.md`

- [ ] **Step 1: Run `pnpm install --frozen-lockfile && pnpm build` in a clean frontend dependency state.**
- [ ] **Step 2: Run `docker compose --profile platform up --build --wait`.**
- [ ] **Step 3: Run `uv run python scripts/e2e_smoke.py --base-url http://127.0.0.1:8100`.**
- [ ] **Step 4: Run the complete Python test suite and OpenSpec strict validation.**
- [ ] **Step 5: Stop disposable Compose state with `docker compose --profile platform down -v`, review the diff, commit, and push without force.**

## Plan Self-Review

- Spec coverage: Tasks 1–2 cover image/runtime/database delivery, Task 3 covers the requested API persistence chain, Task 4 covers CI and docs, and Task 5 supplies fresh integrated proof.
- Placeholder scan: no task defers required P0 behavior.
- Interface consistency: the E2E runner exposes `run_smoke` and `SmokeFailure`; unit and CI callers use those names consistently.
