import pytest

from aqe.models import EvaluationDataset
from aqe.runner import run_release_gate


def test_baseline_profile_passes_every_case():
    evidence = run_release_gate("baseline")

    assert evidence.verdict == "pass"
    assert evidence.dataset_version == "rag-release-gate-v1"
    assert all(result.passed for result in evidence.case_results)


@pytest.mark.parametrize(
    ("profile", "expected_rule"),
    [
        ("wrong-retrieval", "citation-integrity"),
        ("ungrounded-answer", "answer-correctness"),
        ("fabricated-citation", "citation-integrity"),
        ("unsafe-refusal", "refusal"),
        ("prompt-injection-leak", "protected-marker"),
    ],
)
def test_injected_critical_fault_blocks_with_rule_evidence(profile, expected_rule):
    evidence = run_release_gate(profile)

    assert evidence.verdict == "block"
    failed_results = [result for result in evidence.case_results if not result.passed]
    assert failed_results
    assert any(
        finding.rule_id == expected_rule
        for result in failed_results
        for finding in result.findings
    )
    assert {
        finding.rule_id
        for result in failed_results
        for finding in result.findings
    } == {expected_rule}
    assert any(result.case_id in reason for result in failed_results for reason in evidence.reasons)


def test_empty_dataset_escalates_instead_of_passing():
    evidence = run_release_gate("baseline", dataset=EvaluationDataset(version="empty", cases=()))

    assert evidence.verdict == "escalate"
    assert evidence.case_results == ()
    assert evidence.reasons == ("No executable evaluation cases were available.",)


def test_unreadable_dataset_escalates_with_a_validation_reason(monkeypatch):
    def raise_unreadable_dataset():
        raise OSError("fixture file is unavailable")

    monkeypatch.setattr("aqe.runner.load_dataset", raise_unreadable_dataset)

    evidence = run_release_gate("baseline")

    assert evidence.verdict == "escalate"
    assert evidence.case_results == ()
    assert evidence.reasons == ("Dataset validation failed: fixture file is unavailable",)
