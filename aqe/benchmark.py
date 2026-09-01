from __future__ import annotations

from aqe.models import BenchmarkReport, BenchmarkScenario
from aqe.runner import run_release_gate


_CORPUS = "built-in-fixture"
_BOUNDARY = (
    "This benchmark replays deterministic fixture faults only; it does not measure "
    "real-production efficacy or human comparison."
)
_SCENARIOS = (
    ("wrong-retrieval", "citation-integrity"),
    ("ungrounded-answer", "answer-correctness"),
    ("fabricated-citation", "citation-integrity"),
    ("unsafe-refusal", "refusal"),
    ("prompt-injection-leak", "protected-marker"),
)


def _observed_rule_ids(profile: str) -> tuple[str, tuple[str, ...]]:
    evidence = run_release_gate(profile)
    rule_ids = tuple(
        sorted({
            finding.rule_id
            for result in evidence.case_results
            if not result.passed
            for finding in result.findings
        }),
    )
    return evidence.verdict, rule_ids


def run_fixture_benchmark() -> BenchmarkReport:
    """Replay the bounded fixture corpus through the production release gate."""
    scenarios = tuple(
        BenchmarkScenario(
            profile=profile,
            expected_rule_id=expected_rule_id,
            observed_verdict=observed_verdict,
            observed_rule_ids=observed_rule_ids,
            detected=(
                observed_verdict == "block"
                and observed_rule_ids == (expected_rule_id,)
            ),
        )
        for profile, expected_rule_id in _SCENARIOS
        for observed_verdict, observed_rule_ids in (_observed_rule_ids(profile),)
    )
    detected_scenarios = sum(scenario.detected for scenario in scenarios)
    total_scenarios = len(scenarios)
    return BenchmarkReport(
        corpus=_CORPUS,
        boundary=(_BOUNDARY,),
        total_scenarios=total_scenarios,
        detected_scenarios=detected_scenarios,
        missed_scenarios=total_scenarios - detected_scenarios,
        detection_rate=detected_scenarios / total_scenarios if total_scenarios else 0.0,
        scenarios=scenarios,
    )
