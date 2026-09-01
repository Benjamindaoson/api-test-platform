## ADDED Requirements

### Requirement: Benchmark report endpoint
The management API SHALL expose `GET /api/aqe/benchmark` with an explicit response model and return the in-memory deterministic benchmark report without requiring database connectivity.

#### Scenario: Read benchmark report through HTTP
- **WHEN** a client sends `GET /api/aqe/benchmark`
- **THEN** it receives HTTP 200 with the corpus boundary, aggregate counts, detection rate, and every scenario result
