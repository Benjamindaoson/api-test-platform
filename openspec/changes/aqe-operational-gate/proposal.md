## Why

AQE can now evaluate a real RAG target, but its result is an ephemeral, overly detailed console payload. A CI run cannot yet prove what was tested, safely retain the trace, replay a production-like failure, or decide when a code, Prompt, or knowledge change needs the real gate.

## What Changes

- Persist a deterministic, redacted JSON evidence bundle for a real-target gate run.
- Add a replay command that re-runs exactly the case IDs recorded by a prior evidence bundle.
- Add a change-aware CLI that discovers changed files, classifies code/Prompt/knowledge-index impact, and runs or skips the real RAG gate explicitly.
- Add a deterministic tool-call simulator and regression corpus for tool selection, argument validation, permission denial, timeout, and duplicate-call failures.
- Add CI coverage and documentation for the new unattended commands.

## Capabilities

### New Capabilities

- `aqe-evidence-bundles`: durable, redacted and inspectable evidence artifacts for AQE target evaluations.
- `aqe-change-triggered-gate`: safe, non-interactive selection of an AQE real-target gate from a version-control change set.
- `aqe-incident-replay`: reproduction of the case subset captured in a prior AQE evidence bundle.
- `aqe-tool-call-simulation`: deterministic quality regression checks for an Agent's tool-call boundary.

### Modified Capabilities

无。

## Impact

- Adds standard-library-only modules and versioned fixtures beneath `aqe/`, tests, a GitHub Actions workflow, and README commands.
- The commands remain local/CI entry points; no arbitrary-target HTTP endpoint, credentials store, database migration, or automatic code modification is introduced.
