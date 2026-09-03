## 1. Delivery contracts and fixtures

- [x] 1.1 Add failing delivery contract tests for the UI image, Compose profiles, Python image alignment, smoke runner, and CI workflow.
- [x] 1.2 Add repository-owned OpenAPI and pytest fixtures for the disposable smoke flow.

## 2. Reproducible platform runtime

- [x] 2.1 Add the locked pnpm/Next production UI Dockerfile.
- [x] 2.2 Align Python API and LangGraph images with Python 3.13 and `uv.lock`.
- [x] 2.3 Add Compose profiles, health checks, and platform-only dependency ordering.

## 3. End-to-end smoke verification

- [x] 3.1 Implement a retrying, standard-library HTTP smoke runner.
- [x] 3.2 Add unit tests for success and unhealthy-timeout smoke behavior.
- [ ] 3.3 Run the smoke flow against a freshly built Compose platform profile.

## 4. CI and developer delivery

- [x] 4.1 Add independent backend, frontend, and Compose E2E GitHub Actions jobs.
- [x] 4.2 Document the local platform start and smoke commands.

## 5. Verification and release

- [ ] 5.1 Run all Python tests, frontend locked install/build, Compose config/build/up, and smoke verification.
- [ ] 5.2 Validate this OpenSpec change strictly, review the diff, commit, and push the verified P0 change.
