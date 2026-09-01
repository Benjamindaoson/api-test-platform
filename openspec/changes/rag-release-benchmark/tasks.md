## 1. Deterministic benchmark

- [x] 1.1 Add benchmark domain values and the five-scenario fault replay runner.
- [x] 1.2 Add red/green tests for aggregate detection rate, exact expected rules, and a visible corpus boundary.

## 2. API and continuous verification

- [x] 2.1 Add a typed `GET /api/aqe/benchmark` report endpoint and HTTP contract tests.
- [x] 2.2 Add GitHub Actions automation for the locked AQE test suite on `main` pushes and pull requests.

## 3. Documentation and proof

- [x] 3.1 Document benchmark usage, limits, and output in the README.
- [x] 3.2 Validate OpenSpec, run the Python suite, inspect workflow YAML, and perform a local HTTP smoke test.
