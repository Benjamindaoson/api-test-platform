## Context

The FastAPI management API already persists projects, OpenAPI endpoint inventory, test runs, and test results through PostgreSQL. AQE routes can run without the database, but the management workflow cannot. Compose declares all services, yet the UI image definition is absent and CI only protects AQE tests. The project requires Python 3.13 while both existing Python images use 3.12.

## Goals / Non-Goals

**Goals:**

- Make `docker compose --profile platform up --build` start PostgreSQL, Redis, FastAPI, and UI with health checks.
- Make a locked `pnpm install --frozen-lockfile && pnpm build` the container and CI build contract.
- Prove a database-backed HTTP workflow using disposable test data and an OpenAPI fixture.
- Make CI fail before merge if that delivery slice regresses.

**Non-Goals:**

- Starting a production LangGraph/LLM service, calling a real RAG target, or making the UI test workflow dependent on external API keys.
- Replacing the existing agent architecture, adding browser-driven UI assertions, adding authentication, or changing the AQE release-gate semantics.

## Decisions

1. **Use a standalone Node 22 + Corepack pnpm UI image.** It directly runs the locked pnpm installation and Next production build, avoiding a second package manager and matching `packageManager` in `ui/package.json`. A multi-stage build keeps the runtime dependency set isolated from build tooling.
2. **Use Python 3.13 slim images and `uv sync --locked` for Python containers.** The image runtime matches `pyproject.toml`; the lockfile becomes the source of truth rather than the drifting `requirements.txt` file. The API image needs only the management API dependencies, while the LangGraph image retains Node/CodeGraph tooling.
3. **Treat Compose environment variables as the database authority.** Containers receive the same explicit `POSTGRES_*` values, PostgreSQL is initialized through the existing migration mount, and the API reports `ok` only after its connection pool is ready.
4. **Keep the smoke test outside the containers.** `scripts/e2e_smoke.py` uses only Python standard-library HTTP calls and retries `/health`; it exercises public routes as a consumer would. Its fixture OpenAPI document and executable pytest file live under `tests/fixtures/`, are copied into the API image, and do not call a real network target.
5. **Use Compose profiles.** `platform` contains `postgres`, `redis`, `api`, and `ui`; `agent` is opt-in for LangGraph. This gives P0 a reliable no-model path while preserving the agent service for later runtime work.
6. **Use one CI workflow with separate jobs.** Backend checks, UI lockfile/build, and Compose E2E are separate jobs, so a failed UI registry install is visible rather than silently hidden behind AQE-only checks.

## Risks / Trade-offs

- [Docker image builds are slower] → Cache layers by copying lockfiles before application sources; isolate the Compose E2E job.
- [The API test runner executes a file path] → The smoke fixture is repository-owned, static, and invoked only inside the disposable CI/local container; no arbitrary user path is introduced by this change.
- [PostgreSQL may be exposed on a developer machine] → Keep its host port configurable and avoid publishing Redis; use Compose-managed credentials only for local development.
- [UI page behavior is not browser-asserted] → The P0 contract proves production build and HTTP availability; browser flow automation remains an explicitly separate follow-up.
- [LangGraph requires credentials] → Keep it out of the P0 profile and document that it is not part of the management-platform smoke claim.

## Migration Plan

1. Add contract tests and watch them fail for the missing UI image/delivery wiring.
2. Add image, Compose, fixture, and smoke-runner implementation.
3. Run locked frontend build, container builds, full `platform` profile, and the HTTP smoke runner.
4. Add CI gates, then update README with the verified commands and service boundary.
5. If rollout fails, stop the profile with `docker compose --profile platform down -v`; no schema migration beyond the existing idempotent `001_init.sql` is required.

## Open Questions

- None for P0. The user has authorized the current repository and its GitHub remote as the delivery target.
