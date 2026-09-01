## Context

The current release gate has deterministic fault profiles and rule evidence but no aggregate proof that each claimed failure mode is detected. The benchmark must reuse the exact release-gate implementation so it tests the product decision path rather than reimplementing evaluator logic.

## Goals / Non-Goals

**Goals:**

- Replay the five injected faults, calculate detection metrics, and expose a machine-readable report.
- Add CI that continuously protects the deterministic AQE foundation.
- Make the report's limited corpus explicit.

**Non-Goals:**

- Historical incident ingestion, real-service claims, human baselines, LLM judges, or performance benchmarks.
- Persistence, queueing, UI, and new dependencies.

## Decisions

The benchmark has a fixed scenario registry mapping each profile to the exact rule that must block it. It calls `run_release_gate` once per profile, then reports a scenario as detected only when the verdict is `block` and the expected rule appears in evidence. This is stricter than merely counting non-pass verdicts.

The API returns the same typed report through a response model. The GitHub workflow runs the existing tests rather than calling a server because unit/API tests already validate the same route and avoid network flakiness.

Alternative considered: calculate a score directly from evaluator internals. Rejected because that could pass while the runner policy or evidence aggregation is broken.

## Risks / Trade-offs

- [Five fixture scenarios are too narrow] → Report the corpus boundary prominently and treat this only as a regression baseline.
- [Fixed expected rules need maintenance] → A benchmark test fails whenever a profile's detection contract changes.
- [CI does not evaluate a real target] → Real-service adapters and historical replay remain a separate follow-up.

## Migration Plan

Add the module, route, tests, workflow, and README section. Rollback removes these isolated files and route; the existing gate keeps operating.

## Open Questions

- No open question blocks this fixture benchmark. Real-corpus selection requires a design partner and is intentionally deferred.
