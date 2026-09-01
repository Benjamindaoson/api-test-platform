## ADDED Requirements

### Requirement: Evidence-backed incident replay
The system SHALL replay only the case IDs recorded in a compatible evidence bundle and return a new target evidence result.

#### Scenario: Recorded failed case is replayed
- **WHEN** an evidence bundle records a valid case ID for the current dataset version
- **THEN** the replay runs that case against the configured target and identifies the source evidence identifier

#### Scenario: Dataset mismatch blocks unsafe replay
- **WHEN** a bundle dataset version differs from the installed corpus
- **THEN** replay returns `escalate` without calling the target
