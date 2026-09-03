## ADDED Requirements

### Requirement: Independent platform delivery CI gates
The system SHALL run backend tests, a locked frontend production build, and the Compose-backed management smoke flow as independently visible GitHub Actions jobs.

After the Compose smoke creates its project and test run, CI SHALL use a browser
to verify that `/admin` renders the created project and its passed run.

#### Scenario: Frontend dependency or build regression
- **WHEN** `pnpm install --frozen-lockfile` or `pnpm build` fails in the frontend CI job
- **THEN** the workflow fails before the change is treated as delivery-ready

#### Scenario: Database-backed API regression
- **WHEN** the Compose API cannot create, synchronize, execute, persist, or retrieve the smoke workflow data
- **THEN** the Compose E2E CI job fails and emits service logs for diagnosis

#### Scenario: Management UI cannot render the smoke records
- **WHEN** the Compose smoke API flow succeeds but `/admin` cannot display the created project or passed run
- **THEN** the browser verification step fails the Compose E2E CI job

### Requirement: Verified delivery documentation
The repository README SHALL document the tested P0 Compose command, the E2E smoke command, and the boundary that LangGraph/LLM and real RAG quality gates are outside the management-platform smoke profile.

#### Scenario: Developer follows the P0 quickstart
- **WHEN** a developer reads the P0 delivery section
- **THEN** they can start the platform profile, execute the smoke command, and understand which services and credentials are deliberately excluded
