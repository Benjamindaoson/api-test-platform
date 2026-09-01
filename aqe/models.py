from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationCase:
    """One versioned, deterministic RAG quality scenario."""

    id: str
    input: str
    severity: str
    expected_answer_fragment: str
    expected_citations: tuple[str, ...]
    expects_refusal: bool
    protected_markers: tuple[str, ...]
    baseline_answer: str
    baseline_retrieved_document_ids: tuple[str, ...]
    baseline_citations: tuple[str, ...]
    baseline_refused: bool
    alternate_document_id: str = ""


@dataclass(frozen=True)
class EvaluationDataset:
    """A validated, immutable collection of evaluation cases."""

    version: str
    cases: tuple[EvaluationCase, ...]


@dataclass(frozen=True)
class FixtureResponse:
    """Observable output from the deterministic local RAG target."""

    answer: str
    retrieved_document_ids: tuple[str, ...]
    citations: tuple[str, ...]
    refused: bool
    profile: str


@dataclass(frozen=True)
class RuleFinding:
    """One deterministic rule violation preserved in release evidence."""

    rule_id: str
    message: str


@dataclass(frozen=True)
class CaseResult:
    """Evaluation result and response snapshot for one dataset case."""

    case_id: str
    severity: str
    passed: bool
    findings: tuple[RuleFinding, ...]
    response: FixtureResponse
    redaction_markers: tuple[str, ...]


@dataclass(frozen=True)
class EvidencePackage:
    """Complete, inspectable evidence for a single release-gate decision."""

    dataset_version: str
    profile: str
    verdict: str
    reasons: tuple[str, ...]
    case_results: tuple[CaseResult, ...]


@dataclass(frozen=True)
class BenchmarkScenario:
    """Expected and observed result for one deterministic fault replay."""

    profile: str
    expected_rule_id: str
    observed_verdict: str
    observed_rule_ids: tuple[str, ...]
    detected: bool


@dataclass(frozen=True)
class BenchmarkReport:
    """Aggregate result for a clearly bounded AQE benchmark corpus."""

    corpus: str
    boundary: tuple[str, ...]
    total_scenarios: int
    detected_scenarios: int
    missed_scenarios: int
    detection_rate: float
    scenarios: tuple[BenchmarkScenario, ...]
