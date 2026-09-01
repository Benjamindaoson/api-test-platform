## ADDED Requirements

### Requirement: Redacted durable evidence
The system SHALL persist a JSON evidence bundle only after recursively redacting sensitive fields, credential-shaped values, caller-supplied secrets, and local absolute paths.

#### Scenario: Nested target trace contains a credential
- **WHEN** a target trace contains an authorization field or a bearer-token-shaped string
- **THEN** the persisted bundle replaces the value with a redaction marker and retains the surrounding evidence structure

#### Scenario: Evidence writes are inspectable and atomic
- **WHEN** a gate run requests an evidence directory
- **THEN** it writes one valid JSON bundle with a stable evidence identifier and never exposes a partial JSON document at the final path

### Requirement: Safe CLI evidence output
The real-target gate CLI SHALL emit a sanitized representation when it writes or prints operational evidence.

#### Scenario: Target references include a local absolute path
- **WHEN** the CLI serializes target evidence containing a local absolute path
- **THEN** the output does not contain the user-specific path
