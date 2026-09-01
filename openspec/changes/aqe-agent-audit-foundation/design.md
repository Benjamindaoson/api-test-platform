## Context

The local `deep_research` project is a real LangGraph multi-Agent application. Its nodes inspect `message.tool_calls` and `tool` messages, so it provides a concrete source structure for AQE without exposing an unsafe remote execution endpoint. AQE has one verified real incident: EduRAG skipped BOM-prefixed `main.py`, causing `create_app` code retrieval to return a wrong symbol. The current evidence store writes redacted JSON bundles but lacks an audit trail and aggregate decision view.

## Goals / Non-Goals

**Goals:**

- Normalize mapping-shaped LangGraph messages into `ToolCall` records without importing LangGraph or calling a target.
- Evaluate a trace with the existing deterministic tool policy and preserve source message positions.
- Maintain an explicit historical incident contract whose expected behavior is tied to the real fixed defect.
- Add a local append-only hash-chained ledger and role policy interface; provide concise verdict trends.

**Non-Goals:**

- No code changes to `deep_research`, no Agent execution, no external tool invocation, and no claim that a parsed trace validates model reasoning.
- No S3/GCS/Azure implementation, identity provider, encrypted key management, retention deletion, or multi-tenant authorization claim.

## Decisions

### 1. Structural LangGraph adapter

The adapter accepts JSON-compatible messages: assistant messages expose `tool_calls` containing `{name,args}` and tool messages expose `type="tool"`, `name` and optional content. This matches the observed LangGraph usage while avoiding a dependency on a particular SDK. Malformed messages yield structured adapter errors rather than silently disappearing.

### 2. Evidence-backed historical corpus

The first corpus contains only the verified `edurag-bom-code-index` incident: query, expected `create_app` / `main.py` evidence, observed wrong location, root-cause class, and fixed revision. Synthetic simulator profiles remain separate.

### 3. Local append-only audit as a storage seam

`AuditLedger` appends canonical, redacted event records with a previous-record digest. An `AccessPolicy` controls read/write actions for local roles (`system`, `operator`, `auditor`, `viewer`). The ledger is a replaceable backend seam, not an assertion of enterprise IAM.

### 4. Metadata-only trends

Trend calculations consume stored evidence metadata (timestamp, target, verdict, dataset version, evidence ID) and expose counts plus block rate. They intentionally exclude raw answers and traces.

## Risks / Trade-offs

- [LangGraph provider fields differ] → strict structural validation and test fixtures based on the inspected local project.
- [One incident is not a benchmark] → label the corpus `historical-incidents-v1` and expose its size; grow only from verified cases.
- [Local ledger is not tamper-proof across hosts] → hash-chain detects local sequence breaks; use a managed immutable store only after deployment authority exists.
- [Role labels imply full RBAC] → name the API a local policy interface and document the absence of authentication.
