## Why

The repository has a working AQE core but cannot yet prove that the platform shell is deployable: the UI Dockerfile is absent, the frontend build is not part of CI, and the database-backed management workflow has no repeatable end-to-end evidence. This change turns the existing source-level platform into a reproducible local and CI-verified delivery slice.

## What Changes

- Add a production UI container image pinned to the repository's Node and pnpm contract.
- Align Python container images with the Python 3.13 project requirement and make the Compose database configuration a single explicit contract.
- Add a bounded, disposable end-to-end smoke runner that proves project creation, OpenAPI endpoint synchronization, test execution, run persistence, and result retrieval through the running HTTP API.
- Add health checks and a Compose profile suitable for CI; the smoke test runs against PostgreSQL, Redis, and the management API without requiring model credentials or a live RAG target.
- Expand GitHub Actions so Python tests, frontend lockfile installation/build, Compose build, and the end-to-end smoke run are independently visible gates.
- Document the supported delivery command and explicitly distinguish the tested management-platform slice from LangGraph/LLM and real RAG target validation.

## Capabilities

### New Capabilities

- `platform-delivery`: Reproducible UI/API images and a database-connected Compose runtime for the management platform.
- `platform-e2e-smoke`: A disposable HTTP smoke flow that proves persistence-backed API testing behavior.
- `platform-ci-verification`: CI gates that fail on frontend build, image build, or management-platform smoke regressions.

### Modified Capabilities

- None.

## Impact

Affected systems: `ui/`, Dockerfiles, `docker-compose.yml`, FastAPI health/lifecycle behavior, E2E fixtures and scripts, GitHub Actions, README, and delivery tests. No model provider, production RAG target, external object store, SSO, or RBAC integration is introduced.
