## ADDED Requirements

### Requirement: AQE suite runs in pull-request automation
The repository SHALL run the AQE pytest suite through GitHub Actions for pushes to `main` and pull requests targeting `main`.

#### Scenario: Pull request changes AQE code
- **WHEN** a pull request targets `main` with a change under `aqe/`, `api/`, or `tests/`
- **THEN** GitHub Actions installs the locked Python environment and runs `uv run python -m pytest tests`
