## ADDED Requirements

### Requirement: Verified historical incident corpus
The system SHALL store historical regressions separately from synthetic fault profiles and identify their source revision and expected repaired behavior.

#### Scenario: EduRAG code-index incident remains reproducible
- **WHEN** the historical corpus is loaded
- **THEN** it includes the verified BOM-index incident with expected `create_app` and `main.py` evidence
