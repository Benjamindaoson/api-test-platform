## Context

The existing platform is a FastAPI management API backed by optional PostgreSQL persistence plus a LangGraph-oriented agent workflow. Its current test run records describe pytest executions and cannot represent a RAG response, an evaluator decision, or a release-level verdict. The first AQE release must be repeatable in a developer checkout and CI, so it cannot require an API key, a vector database, a model provider, or a reachable business service.

## Goals / Non-Goals

**Goals:**

- Prove a full unattended quality-gate loop against a deterministic RAG target.
- Make every verdict inspectable from versioned data, response snapshots, and deterministic evaluator findings.
- Cover the initial critical failure classes: wrong retrieval, ungrounded answer, fabricated citation, missing refusal, and prompt-injection leakage.
- Expose the loop through a small FastAPI interface that works when PostgreSQL is unavailable.

**Non-Goals:**

- Calling an external LLM, embedding model, vector database, or real customer service.
- Persisting runs, building UI, authenticating users, scheduling CI, or auto-repairing code.
- Replacing model-based semantic evaluation in later releases; this change establishes the deterministic release-blocking foundation first.

## Decisions

### Use a deterministic fixture target instead of a real model-backed RAG service

The fixture reads a versioned local dataset and emits a complete response shape. A named profile deterministically injects one failure. This permits red/green tests for the evaluator and reliable regression runs.

Alternative considered: call a hosted model and local vector store. Rejected for this change because output variability, secret management, cost, and infrastructure would obscure whether a gate failure is caused by the evaluator or target.

### Separate domain data, fixture behavior, evaluation, and orchestration

The new `aqe` package has four boundaries:

- `models.py`: immutable domain values and JSON serialization helpers.
- `dataset.py`: validation and loading of the versioned JSON data.
- `fixture.py`: target behavior and fault injection only.
- `evaluators.py` and `runner.py`: deterministic findings and policy verdict.

The FastAPI route imports only the runner, making a future real-service adapter possible without modifying evaluator or policy behavior.

Alternative considered: place all logic in `api/main.py`. Rejected because target behavior, evaluation, and API transport have different reasons to change and require independent tests.

### Make evidence an in-memory structured contract

`run_release_gate(profile)` returns an `EvidencePackage` containing dataset version, active profile, case results, verdict, and reasons. It is returned directly by the HTTP API for v0.1. Database persistence is deliberately deferred until the evidence contract is proven stable.

Alternative considered: reuse `test_runs` and `test_results`. Rejected because their API-testing fields cannot faithfully store retrieval evidence, evaluator rule identifiers, or a release verdict without an unrelated schema migration.

### Use deterministic evaluators for release-blocking decisions

The first gate checks expected answer fragments, required and retrieved citations, refusal status, and protected markers. It does not use an LLM judge for a blocking verdict.

Alternative considered: an LLM judge from the first release. Rejected because it creates uncalibrated and non-repeatable release decisions. LLM judges can later be appended as non-blocking evidence after a calibration dataset exists.

## Risks / Trade-offs

- [Fixture success does not prove real-service integration] → Treat the fixture as a test target, then add a separately specified adapter and benchmark against historical incidents.
- [Substring answer evaluation is narrow] → Keep it only for the deterministic baseline; introduce calibrated semantic evaluation as a later capability rather than overclaiming language understanding.
- [Synchronous execution does not scale] → Dataset is intentionally small; add queueing only when a real-service adapter creates long-running work.
- [Evidence contains potential sensitive content in a future target] → This fixture contains no secrets; future adapters require redaction and retention controls before persistence.

## Migration Plan

1. Add the package, dataset, routes, and unit/API tests with no change to existing test-run tables.
2. Run the fixture gate in local development and CI as a self-test of AQE behavior.
3. Add a new persistence schema only after the evidence package contract is accepted and an actual deployment requires run history.
4. Roll back by removing the `/api/aqe/*` routes and `aqe/` package; no existing API route or database table changes are required.

## Open Questions

- No open questions block this deterministic first slice. Real-service adapters, persistence, LLM judging, and UI are explicitly deferred to later changes.
