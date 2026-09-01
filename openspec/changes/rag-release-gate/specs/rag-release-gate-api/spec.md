## ADDED Requirements

### Requirement: Fixture inspection endpoint
The management API SHALL expose `GET /api/aqe/fixture` and return the fixture dataset version, supported fault profiles, and case metadata without revealing protected marker values.

#### Scenario: Inspect fixture capabilities
- **WHEN** a client sends `GET /api/aqe/fixture`
- **THEN** it receives HTTP 200 with the dataset version, profiles, and case identifiers

### Requirement: Unattended release-gate endpoint
The management API SHALL expose `POST /api/aqe/runs` accepting an optional `profile` field. It MUST execute the complete dataset synchronously for the local fixture target and return a structured evidence package without requiring database connectivity.

#### Scenario: Baseline release gate via HTTP
- **WHEN** a client posts `{ "profile": "baseline" }` to `/api/aqe/runs`
- **THEN** it receives HTTP 200 with a `pass` verdict and evidence for every dataset case

#### Scenario: Unknown profile is rejected
- **WHEN** a client posts an unsupported profile to `/api/aqe/runs`
- **THEN** it receives HTTP 422 and no evidence package
