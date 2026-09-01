## 1. Evidence safety

- [x] 1.1 Add recursive trace redaction and atomic JSON evidence persistence with regression tests.
- [x] 1.2 Integrate optional persisted, redacted evidence output into the real RAG gate CLI.

## 2. Repeatable target quality checks

- [x] 2.1 Add case-subset execution and an incident replay CLI with dataset compatibility checks.
- [x] 2.2 Add a change-aware gate CLI for explicit paths and Git diffs, including no-impact behavior.

## 3. Agent tool boundary

- [x] 3.1 Add a deterministic tool-call simulator and versioned failure corpus.
- [x] 3.2 Add a tool quality gate and benchmark tests for selection, argument, permission, timeout and duplicate failures.

## 4. Delivery

- [x] 4.1 Add CI verification and document local/CI commands, limits and evidence boundaries.
- [x] 4.2 Run the complete suite, strict OpenSpec validation, compile checks, and relevant CLI smoke tests.
