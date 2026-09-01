from __future__ import annotations

from aqe.dataset import load_dataset
from aqe.evaluators import evaluate_case
from aqe.fixture import run_fixture, supported_profiles
from aqe.models import EvidencePackage, EvaluationDataset


def _escalated_evidence(dataset_version: str, profile: str, reason: str) -> EvidencePackage:
    return EvidencePackage(
        dataset_version=dataset_version,
        profile=profile,
        verdict="escalate",
        reasons=(reason,),
        case_results=(),
    )


def run_release_gate(
    profile: str = "baseline",
    dataset: EvaluationDataset | None = None,
) -> EvidencePackage:
    """Run every case and return an evidence-backed release verdict."""
    if profile not in supported_profiles():
        accepted = ", ".join(supported_profiles())
        raise ValueError(f"Unknown AQE fixture profile '{profile}'. Accepted profiles: {accepted}")

    if dataset is None:
        try:
            dataset = load_dataset()
        except (OSError, ValueError) as error:
            return _escalated_evidence("unavailable", profile, f"Dataset validation failed: {error}")

    if not dataset.cases:
        return _escalated_evidence(
            dataset.version,
            profile,
            "No executable evaluation cases were available.",
        )

    case_results = tuple(
        evaluate_case(case, run_fixture(case, profile))
        for case in dataset.cases
    )
    critical_failures = [
        result for result in case_results
        if not result.passed and result.severity == "critical"
    ]
    if critical_failures:
        reasons = tuple(
            f"Critical case '{result.case_id}' failed rules: "
            f"{', '.join(finding.rule_id for finding in result.findings)}."
            for result in critical_failures
        )
        return EvidencePackage(
            dataset_version=dataset.version,
            profile=profile,
            verdict="block",
            reasons=reasons,
            case_results=case_results,
        )

    non_critical_failures = [result for result in case_results if not result.passed]
    if non_critical_failures:
        reasons = tuple(
            f"Non-critical case '{result.case_id}' failed and requires review."
            for result in non_critical_failures
        )
        return EvidencePackage(
            dataset_version=dataset.version,
            profile=profile,
            verdict="escalate",
            reasons=reasons,
            case_results=case_results,
        )

    return EvidencePackage(
        dataset_version=dataset.version,
        profile=profile,
        verdict="pass",
        reasons=("All executable evaluation cases passed.",),
        case_results=case_results,
    )
