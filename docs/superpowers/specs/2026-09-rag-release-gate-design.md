# RAG Release Gate Design

**Purpose:** build the first executable Agent Quality Engineer vertical slice: a deterministic RAG target that the platform can evaluate and turn into an explainable release verdict.

## Architecture

The feature lives in a standalone Python package named `aqe`. The dataset loader produces typed `EvaluationCase` values; the fixture turns one case and one profile into a typed response; evaluators turn that response into rule findings; and the runner aggregates those findings into an `EvidencePackage`.

`api/main.py` remains a transport layer. It exposes fixture metadata and delegates a requested profile to `run_release_gate`. It neither knows the dataset schema nor reimplements any quality rule. No run is persisted in the existing API-test tables because those tables cannot describe retrieval, citations, or evaluator evidence.

```text
rag_release_gate_v1.json
        ↓
dataset.py → EvaluationCase
        ↓
fixture.py(profile) → FixtureResponse
        ↓
evaluators.py → RuleFinding[]
        ↓
runner.py → EvidencePackage(verdict, reasons, case results)
        ↓
POST /api/aqe/runs
```

## Interfaces

- `load_dataset() -> EvaluationDataset`: loads and validates the checked-in JSON file.
- `run_fixture(case: EvaluationCase, profile: FaultProfile) -> FixtureResponse`: emits a deterministic response; unknown inputs refuse.
- `evaluate_case(case: EvaluationCase, response: FixtureResponse) -> CaseResult`: executes deterministic rules and preserves the response snapshot.
- `run_release_gate(profile: str = "baseline") -> EvidencePackage`: evaluates every case and applies the release policy.

## Release Policy

- Every executable case passes: `pass`.
- A failed `critical` case: `block`.
- An invalid dataset, no executable cases, or a non-critical unexpected failure: `escalate`.

The first slice intentionally treats the LLM judge as absent. A release-blocking rule must be deterministic and traceable to the exact response field it inspected.

## Dataset and Faults

The dataset has three cases: a factual answer with a required citation, an out-of-scope request that requires refusal, and a prompt-injection request that requires refusal and must never contain the protected marker. Fault profiles produce a predictable violation: wrong retrieval, ungrounded answer, fabricated citation, unsafe refusal, or prompt-injection leak.

## Testing

Tests first define the desired API and policy. Unit tests run entirely in process. API tests use FastAPI's `TestClient`; the new routes do not touch PostgreSQL, so they remain executable when the optional database is absent. A process-level smoke test starts Uvicorn and sends a real HTTP request to `/api/aqe/runs`.

## Deferred Work

Real RAG/Agent adapters, asynchronous queueing, PostgreSQL persistence, authorization, UI, semantic LLM judging, CI integration, and benchmark comparisons belong to separate changes. The evidence contract created here is the integration point for all of them.
