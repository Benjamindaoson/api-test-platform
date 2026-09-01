## 1. Target contract and corpus

- [x] 1.1 Add typed StuckToShip target response and versioned four-route evaluation corpus.
- [x] 1.2 Add failing tests for response normalization, safe contract failures and corpus coverage.

## 2. Read-only adapter and evidence gate

- [x] 2.1 Implement the injected HTTP transport, non-streaming request contract and safe response parsing.
- [x] 2.2 Implement target route, citation and clarification rules with pass/block/escalate verdicts.
- [x] 2.3 Add a non-interactive JSON CLI that reads only local arguments/environment configuration.

## 3. Verification and documentation

- [x] 3.1 Run focused tests, the complete AQE suite, compile checks and strict OpenSpec validation.
- [x] 3.2 Start the local EduRAG target and execute the real HTTP smoke run without mutating target knowledge or state.
- [x] 3.3 Document the target contract, local run command, result boundary and CI handoff.
