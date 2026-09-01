## ADDED Requirements

### Requirement: Versioned StuckToShip evaluation corpus
The system SHALL define a versioned corpus with stable cases spanning course, code, FAQ and clarify routes.

#### Scenario: Corpus exposes its intended routes
- **WHEN** the StuckToShip corpus is loaded
- **THEN** it contains at least one case for each of `course`, `code`, `faq` and `clarify`

### Requirement: Evidence-backed target verdict
The system SHALL return `pass` only when every target response satisfies its expected route, required answer fragments, and citation/clarification policy; it SHALL return `block` for an evaluable rule failure and `escalate` for a target execution failure.

#### Scenario: Missing citation blocks an answerable case
- **WHEN** a valid target response has the expected answerable route but no reference
- **THEN** the resulting evidence verdict is `block` and contains a `citation-presence` finding

#### Scenario: Wrong code symbol blocks an otherwise cited response
- **WHEN** a code-route response includes citations but omits the case's required symbol or source-file fragment
- **THEN** the resulting evidence verdict is `block` and contains an `answer-correctness` finding

#### Scenario: Target outage escalates validation
- **WHEN** the adapter cannot reach the target
- **THEN** the resulting evidence verdict is `escalate` and contains the safe execution-failure reason

### Requirement: Local unattended runner
The system SHALL provide a command-line entry point that executes the target corpus with no interactive input and emits JSON evidence.

#### Scenario: Base URL defaults locally
- **WHEN** the command runs without a base URL argument or environment override
- **THEN** it targets `http://127.0.0.1:8010`.
