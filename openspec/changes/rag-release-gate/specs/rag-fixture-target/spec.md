## ADDED Requirements

### Requirement: Deterministic fixture responses
The system SHALL provide a local fixture RAG target that returns a deterministic response for every supported evaluation input and fault profile. A response MUST contain an answer, retrieved document identifiers, citation identifiers, a refusal flag, and the active profile name.

#### Scenario: Baseline response for a supported question
- **WHEN** the fixture receives a supported evaluation question with the `baseline` profile
- **THEN** it returns the configured answer, retrieved documents, citations, and refusal behavior from the versioned fixture data

#### Scenario: Unsupported input remains inspectable
- **WHEN** the fixture receives an input that does not match a configured evaluation question
- **THEN** it returns a refusal response with no citations and no retrieved documents

### Requirement: Named fault profiles
The fixture SHALL support the named profiles `baseline`, `wrong-retrieval`, `ungrounded-answer`, `fabricated-citation`, `unsafe-refusal`, and `prompt-injection-leak`. Each non-baseline profile MUST alter a single observable failure condition while preserving a deterministic response shape.

#### Scenario: Wrong retrieval is injected
- **WHEN** the fixture runs a case that requires a citation under the `wrong-retrieval` profile
- **THEN** the response contains a retrieved document identifier that is not the required document identifier

#### Scenario: Prompt injection leakage is injected
- **WHEN** the fixture receives the injection-resistance case under the `prompt-injection-leak` profile
- **THEN** the response contains the configured protected marker while retaining the case's baseline refusal status
