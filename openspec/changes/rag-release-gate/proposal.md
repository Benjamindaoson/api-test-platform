## Why

The platform can generate and execute API tests, but it cannot currently prove whether a RAG application remains grounded, cites valid sources, refuses unsafe requests, or withstands prompt injection after a release change. A deterministic internal target is required before the product can make credible release-quality claims against real customer systems.

## What Changes

- Add a deterministic fixture RAG service with a versioned knowledge base and named fault profiles.
- Add a versioned RAG evaluation dataset covering answer correctness, grounding, citation integrity, refusal behavior, and prompt-injection resistance.
- Add deterministic evaluators and a release policy that returns `pass`, `block`, or `escalate` with structured evidence.
- Add management API endpoints to inspect the fixture and execute a release-gate run without requiring a database, model provider, vector database, or external network call.
- Add automated tests that prove the baseline profile passes and each injected critical failure blocks the release.

## Capabilities

### New Capabilities

- `rag-fixture-target`: Deterministic local RAG target with observable, named fault profiles.
- `rag-release-evaluation`: Versioned dataset, deterministic evaluators, evidence package, and release verdict policy.
- `rag-release-gate-api`: HTTP interface for fixture inspection and unattended release-gate execution.

### Modified Capabilities

- None.

## Impact

- New Python package under `aqe/` and a versioned JSON dataset under `aqe/fixtures/`.
- New FastAPI request and response models plus `/api/aqe/*` routes in `api/main.py`.
- New pytest suite under `tests/`.
- No database migration, frontend change, model-provider call, or new third-party dependency in this change.
