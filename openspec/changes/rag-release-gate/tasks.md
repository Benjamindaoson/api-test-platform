## 1. Deterministic RAG target

- [x] 1.1 Add the immutable AQE domain model, dataset loader, and validated versioned fixture data.
- [x] 1.2 Add the deterministic fixture RAG target and named fault profiles.
- [x] 1.3 Add red/green unit tests for baseline responses, unknown inputs, and every fault profile.

## 2. Quality evaluation and policy

- [x] 2.1 Add deterministic answer, citation, refusal, and protected-marker evaluators.
- [x] 2.2 Add the release-gate runner and `pass` / `block` / `escalate` policy.
- [x] 2.3 Add red/green tests that prove baseline passes and every injected critical fault blocks with evidence.

## 3. Management API integration

- [x] 3.1 Add fixture-inspection and release-gate Pydantic models and FastAPI routes.
- [x] 3.2 Add HTTP tests for fixture inspection, a baseline pass, a fault-profile block, and unknown-profile validation.

## 4. Documentation and verification

- [x] 4.1 Document the local AQE fixture workflow and supported profiles in the README.
- [x] 4.2 Run OpenSpec validation, the AQE pytest suite, compile checks, and a live local API smoke test.
