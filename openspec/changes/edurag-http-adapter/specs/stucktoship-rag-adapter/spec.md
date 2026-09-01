## ADDED Requirements

### Requirement: StuckToShip non-streaming adapter
The system SHALL issue only a non-streaming `POST {base_url}/api/v1/rag/ask` request with a case query and isolated AQE session ID, and SHALL normalize a successful StuckToShip response into answer, references, route and trace data.

#### Scenario: Successful target response is normalized
- **WHEN** the target returns `code: 0` with an answer, references, route and trace in `data`
- **THEN** the adapter returns those values as a typed target response without changing reference identity

#### Scenario: Optional key is not evidence
- **WHEN** an API key is supplied through the configured environment variable
- **THEN** the adapter sends it only as an Authorization header and no returned evidence or error reason contains the key

### Requirement: Target contract failures are explicit
The system SHALL treat a network failure, non-success HTTP response, non-zero target code, malformed JSON, or missing required response field as a target execution failure.

#### Scenario: Target contract is incomplete
- **WHEN** the target returns a JSON body without `data.route` or `data.trace`
- **THEN** the adapter reports a contract failure instead of manufacturing a default route or trace

### Requirement: No arbitrary target management API
The system SHALL NOT expose an HTTP endpoint in the API test platform that accepts an arbitrary target URL for this adapter.

#### Scenario: Platform OpenAPI remains fixture-only for AQE runs
- **WHEN** a client reads the platform OpenAPI schema after this change
- **THEN** it does not find a new AQE endpoint that accepts a `base_url` field
