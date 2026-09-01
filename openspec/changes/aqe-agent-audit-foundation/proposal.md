## Why

AQE can test a simulated tool boundary, but it cannot yet assess a trace emitted by a real LangGraph Agent or distinguish a verified historical incident from a synthetic fault. Evidence is also persisted without an append-only audit view or a quality trend summary.

## What Changes

- Add a read-only adapter for LangGraph/LangChain message traces, including declared tool calls and returned tool messages.
- Add a versioned historical-incident corpus beginning with the verified EduRAG BOM code-index incident.
- Add a local append-only audit ledger, role-based access policy interface, and trend summary over evidence metadata.
- Preserve the existing filesystem bundle backend as the default storage implementation; do not claim a cloud object-store integration without credentials and retention policy.

## Capabilities

### New Capabilities

- `langgraph-agent-trace-adapter`: normalize real LangGraph message tool calls into AQE's tool-boundary contract.
- `aqe-historical-incidents`: record versioned, evidence-backed real incidents for regression replay.
- `aqe-audit-and-trends`: record access-controlled local audit events and summarize release quality trends.

### Modified Capabilities

无。

## Impact

- Adds AQE modules, fixtures, tests and local CLI/API-neutral contracts.
- Does not modify or execute the candidate Agent's tools, send prompts, require cloud credentials, or introduce SSO.
