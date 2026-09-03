## ADDED Requirements

### Requirement: Persistence-backed management smoke flow
The system SHALL provide a repeatable smoke runner that waits for a healthy FastAPI database connection and then creates a project, synchronizes a supplied OpenAPI document, executes a supplied pytest file, retrieves the persisted run, and verifies the stored endpoint inventory.

#### Scenario: Smoke flow completes against disposable Compose services
- **WHEN** the `platform` Compose profile is healthy and the smoke runner is invoked with the FastAPI base URL
- **THEN** the runner reports a created project ID, a persisted test-run ID, one or more synchronized endpoints, and a passed test run

#### Scenario: API never becomes database healthy
- **WHEN** the health endpoint remains degraded until the runner timeout expires
- **THEN** the runner exits unsuccessfully with endpoint and last-response context rather than treating the API as ready

### Requirement: No external quality-system dependency
The smoke runner SHALL use only repository-owned OpenAPI and pytest fixtures and SHALL NOT call a model provider, real RAG target, or arbitrary remote API.

#### Scenario: CI runs without provider credentials
- **WHEN** the smoke runner is executed in CI without OpenAI, LangSmith, or RAG credentials
- **THEN** the management-platform workflow completes using only the Compose services and repository fixtures
