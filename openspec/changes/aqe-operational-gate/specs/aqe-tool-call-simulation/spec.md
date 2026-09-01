## ADDED Requirements

### Requirement: Deterministic tool-call policy simulation
The system SHALL simulate declared Agent tool calls without external side effects and produce structured results for tool selection, required arguments, permission, timeout, and duplicate invocation.

#### Scenario: Unauthorized call is blocked
- **WHEN** a planned call targets a tool disallowed for the caller role
- **THEN** the tool gate returns `block` with a `tool-permission` finding

#### Scenario: Versioned injected failures are detected
- **WHEN** the built-in tool simulator corpus replays its declared fault profiles
- **THEN** every profile yields the expected finding and a `block` verdict
