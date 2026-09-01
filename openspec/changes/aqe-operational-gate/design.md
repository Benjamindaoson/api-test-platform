## Context

The current StuckToShip gate emits useful structured evidence but keeps it only in process memory and prints raw target trace content. The fixture benchmark proves AQE rule behavior, while a production-like release loop also needs reproducible evidence, a way to replay incidents, change-scoped invocation, and a controlled boundary for tool-using Agents.

## Goals / Non-Goals

**Goals:**

- Store redacted JSON bundles atomically on the local filesystem and preserve the case-level verdict evidence needed for replay.
- Redact credential-shaped values, sensitive-key fields and local absolute paths recursively before persistence or CLI output.
- Classify explicit file paths or `git diff --name-only` paths into code, Prompt, and knowledge/index impact; execute the target gate only for a relevant change.
- Replay the exact recorded target cases and fail safely when the dataset version or case IDs are unavailable.
- Simulate the Agent tool boundary without executing external tools.

**Non-Goals:**

- No database, object-store, RBAC/SSO, retention policy, remote URL API, or automatic code repair.
- No claim that the compact tool corpus measures general Agent reliability or replaces live tool integration tests.
- No automatic re-indexing, prompting, deployment or Git push.

## Decisions

### 1. Filesystem JSON bundles with content-derived identifiers

`EvidenceStore` writes one redacted JSON document under a caller-selected directory. Its identifier is a SHA-256 prefix of canonical redacted evidence, which makes the same evidence easy to compare without relying on a database. Atomic replace avoids partially written bundles.

The alternative, a database table, would couple the first CI-ready slice to the management API's optional database and migration path. It is deferred.

### 2. One recursive sanitizer at every persistence and CLI boundary

The redactor works on JSON-compatible trees. It removes values in sensitive fields, common bearer/key token shapes, explicit supplied secrets, and machine-specific absolute paths. Internal evaluator objects stay untouched so that test logic remains exact; only serialized outputs are sanitized.

The alternative, redacting individual response fields, is fragile because target traces are nested and evolve independently.

### 3. Explicit, conservative change selection

`aqe.change_gate` accepts repeated `--changed-file` paths for CI and falls back to a git diff. Python/source/config files, Prompt/template files, and knowledge/index artifacts trigger the real gate. An unrelated change returns `not_applicable`, records no false pass, and exits zero. The caller must still supply a permitted local target origin through the existing StuckToShip adapter configuration.

### 4. Replay by recorded case identifiers

Replay reads a persisted bundle, validates its dataset version, and invokes the same target gate for its recorded case IDs. A missing or unknown case is an `escalate`, never silently replaced with the whole suite.

### 5. Deterministic tool simulator, not a fake browser or shell

The simulator accepts a declared tool contract and planned calls. It returns structured outcomes for unknown tools, missing arguments, permission denial, timeouts and duplicate calls. A versioned corpus checks that each injected failure blocks the tool gate. This isolates policy evaluation from irreversible external execution.

## Risks / Trade-offs

- [A novel secret format escapes redaction] → allow callers to pass explicit secrets; never persist HTTP headers; keep the pattern list tested and conservative.
- [Path classification misses an organisation-specific layout] → allow explicit changed paths and document the default classifier; an unclassified path is visible as `not_applicable` rather than a pass.
- [A saved incident cannot be replayed after corpus evolution] → require an exact dataset version and emit `escalate` with the incompatibility.
- [Simulator diverges from an actual tool provider] → label it as a policy regression corpus and retain live adapter testing as a separate direction.

## Migration Plan

1. Add modules and tests without changing existing fixture or HTTP-gate behavior.
2. Make persistence opt-in through CLI arguments, so current users receive the same verdict payload.
3. Add a CI workflow that tests the deterministic operational layer only; target repositories can call the real command after starting their own service.
4. Roll back by removing the new workflow and optional commands; existing AQE gates remain independent.
