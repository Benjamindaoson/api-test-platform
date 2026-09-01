## ADDED Requirements

### Requirement: Local append-only audit policy
The system SHALL enforce declared local role permissions before appending or reading audit events and SHALL chain each event to the prior event digest.

#### Scenario: Viewer cannot append an audit event
- **WHEN** a `viewer` attempts a write action
- **THEN** the ledger rejects the request without changing the audit file

### Requirement: Metadata-only trend summary
The system SHALL summarize verdict counts and block rate from evidence metadata without exposing raw answers or traces.

#### Scenario: A mixed verdict series is summarized
- **WHEN** stored events contain pass, block and escalate verdicts
- **THEN** the summary returns all counts and a block rate based on terminal evaluated decisions
