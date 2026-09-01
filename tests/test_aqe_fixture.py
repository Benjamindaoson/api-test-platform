from dataclasses import replace

import pytest

from aqe.dataset import _load_case, load_dataset
from aqe.fixture import run_fixture, run_fixture_for_input, supported_profiles


def test_baseline_returns_grounded_answer_with_required_citation():
    case = load_dataset().cases[0]

    response = run_fixture(case, "baseline")

    assert case.expected_answer_fragment in response.answer
    assert response.citations == case.expected_citations
    assert response.refused is False
    assert response.retrieved_document_ids == case.expected_citations


def test_unknown_input_refuses_without_evidence():
    response = run_fixture_for_input("How do I deploy a satellite?", "baseline")

    assert response.refused is True
    assert response.citations == ()
    assert response.retrieved_document_ids == ()


def test_fixture_uses_configured_response_refusal_not_evaluator_expectation():
    baseline_case = load_dataset().cases[0]
    fixture_case = replace(
        baseline_case,
        expects_refusal=False,
        baseline_refused=True,
    )

    response = run_fixture(fixture_case, "baseline")

    assert response.refused is True


@pytest.mark.parametrize(
    ("profile", "case_id"),
    [
        ("wrong-retrieval", "remote-work-policy"),
        ("ungrounded-answer", "remote-work-policy"),
        ("fabricated-citation", "remote-work-policy"),
        ("unsafe-refusal", "out-of-scope-refusal"),
        ("prompt-injection-leak", "prompt-injection-refusal"),
    ],
)
def test_fault_profiles_change_their_target_case(profile, case_id):
    case = next(case for case in load_dataset().cases if case.id == case_id)

    response = run_fixture(case, profile)

    assert response.profile == profile
    assert response != run_fixture(case, "baseline")


def test_supported_profiles_are_a_stable_public_contract():
    assert supported_profiles() == (
        "baseline",
        "wrong-retrieval",
        "ungrounded-answer",
        "fabricated-citation",
        "unsafe-refusal",
        "prompt-injection-leak",
    )


def test_dataset_rejects_answer_case_without_expected_answer_contract():
    with pytest.raises(ValueError, match="expected_answer_fragment"):
        _load_case(
            {
                "id": "missing-answer-contract",
                "input": "What is the policy?",
                "severity": "critical",
                "expected_citations": [],
                "expects_refusal": False,
                "protected_markers": [],
                "baseline_response": {
                    "answer": "A response without an evaluation contract.",
                    "retrieved_document_ids": [],
                    "citations": [],
                    "refused": False,
                },
            },
        )
