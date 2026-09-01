## ADDED Requirements

### Requirement: Deterministic fault-replay measurement
The system SHALL replay the five non-baseline fixture profiles through the existing release gate and produce a benchmark report containing every scenario, expected blocking rule, observed verdict, observed rule identifiers, and detection status.

#### Scenario: Current fixture corpus is fully detected
- **WHEN** the benchmark runs against the unchanged local fixture corpus
- **THEN** it reports five scenarios, five detections, zero misses, and a detection rate of `1.0`

### Requirement: Benchmark does not overclaim production efficacy
The benchmark report SHALL identify itself as the `built-in-fixture` corpus and SHALL not label its detection rate as a real-production or human-comparison result.

#### Scenario: Benchmark metadata states corpus boundary
- **WHEN** a client reads the benchmark report
- **THEN** it receives the corpus identifier `built-in-fixture` and a boundary statement that historical incidents and real services are not included
