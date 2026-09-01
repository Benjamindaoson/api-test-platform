## Why

The RAG Release Gate can return a verdict for one profile, but it does not quantify whether the gate detects the known high-risk failures it claims to cover. Without a repeatable benchmark report, the project cannot establish a measurement baseline before it connects to historical incidents or a real RAG service.

## What Changes

- Add a deterministic benchmark suite that replays every injected fixture fault against the existing release gate.
- Calculate total scenarios, detected scenarios, missed scenarios, detection rate, and per-scenario evidence references.
- Add a read-only management API endpoint for the benchmark report and a GitHub Actions workflow that runs the AQE test suite on pushes and pull requests.
- Document the benchmark's boundary: it validates the built-in fault corpus only and does not prove effectiveness against real production failures.

## Capabilities

### New Capabilities

- `rag-release-benchmark`: Deterministic fault-replay benchmark and machine-readable report for the local RAG Release Gate.
- `aqe-ci-verification`: Automated execution of the AQE suite in GitHub Actions.
- `rag-release-benchmark-api`: Read-only management API endpoint for the benchmark report.

### Modified Capabilities

- None.

## Impact

- New benchmark module and pytest coverage under `aqe/` and `tests/`.
- One new FastAPI route and response model in `api/main.py`.
- One GitHub Actions workflow under `.github/workflows/`.
- README, OpenSpec artifacts, and product plan updates; no new runtime dependency, data migration, model call, or external target.
