## ADDED Requirements

### Requirement: Conservative change-triggered real gate
The system SHALL classify code, Prompt/template, and knowledge/index changes as AQE-relevant and run the configured real-target gate for those changes.

#### Scenario: Prompt change invokes the target gate
- **WHEN** the change set contains a Prompt or template file
- **THEN** the command executes the target gate and returns its evidence verdict

#### Scenario: Unrelated change is explicit
- **WHEN** no changed path matches the AQE relevance classifier
- **THEN** the command returns `not_applicable`, explains that no target gate was run, and does not claim a quality pass

### Requirement: Change source supports CI and local use
The command SHALL accept repeated explicit changed-file arguments and SHALL otherwise attempt to read a Git name-only diff.

#### Scenario: CI passes explicit paths
- **WHEN** one or more `--changed-file` arguments are supplied
- **THEN** no Git command is required to classify the change set
