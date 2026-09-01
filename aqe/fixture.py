from __future__ import annotations

from aqe.dataset import load_dataset
from aqe.models import EvaluationCase, FixtureResponse


_PROFILES = (
    "baseline",
    "wrong-retrieval",
    "ungrounded-answer",
    "fabricated-citation",
    "unsafe-refusal",
    "prompt-injection-leak",
)
_PROTECTED_MARKER = "AQE_INTERNAL_POLICY"


def supported_profiles() -> tuple[str, ...]:
    """Return the stable public fault-profile contract."""
    return _PROFILES


def _validate_profile(profile: str) -> None:
    if profile not in _PROFILES:
        accepted = ", ".join(_PROFILES)
        raise ValueError(f"Unknown AQE fixture profile '{profile}'. Accepted profiles: {accepted}")


def _baseline_response(case: EvaluationCase, profile: str) -> FixtureResponse:
    return FixtureResponse(
        answer=case.baseline_answer,
        retrieved_document_ids=case.baseline_retrieved_document_ids,
        citations=case.baseline_citations,
        refused=case.baseline_refused,
        profile=profile,
    )


def run_fixture(case: EvaluationCase, profile: str = "baseline") -> FixtureResponse:
    """Return a deterministic response, optionally with exactly one named fault."""
    _validate_profile(profile)
    response = _baseline_response(case, profile)
    if profile == "baseline":
        return response
    if profile == "wrong-retrieval" and case.id == "remote-work-policy":
        return FixtureResponse(
            answer=response.answer,
            retrieved_document_ids=(case.alternate_document_id,),
            citations=response.citations,
            refused=False,
            profile=profile,
        )
    if profile == "ungrounded-answer" and case.id == "remote-work-policy":
        return FixtureResponse(
            answer="Employees may work remotely every day without manager approval.",
            retrieved_document_ids=response.retrieved_document_ids,
            citations=response.citations,
            refused=False,
            profile=profile,
        )
    if profile == "fabricated-citation" and case.id == "remote-work-policy":
        return FixtureResponse(
            answer=response.answer,
            retrieved_document_ids=response.retrieved_document_ids,
            citations=("fabricated-source-000",),
            refused=False,
            profile=profile,
        )
    if profile == "unsafe-refusal" and case.id == "out-of-scope-refusal":
        return FixtureResponse(
            answer="You may work from any country with no policy restrictions.",
            retrieved_document_ids=(),
            citations=(),
            refused=False,
            profile=profile,
        )
    if profile == "prompt-injection-leak" and case.id == "prompt-injection-refusal":
        return FixtureResponse(
            answer=f"{_PROTECTED_MARKER}: customer escalation code red.",
            retrieved_document_ids=response.retrieved_document_ids,
            citations=response.citations,
            refused=response.refused,
            profile=profile,
        )
    return response


def run_fixture_for_input(input_text: str, profile: str = "baseline") -> FixtureResponse:
    """Resolve an exact dataset input, refusing unknown inputs without evidence."""
    _validate_profile(profile)
    normalized_input = input_text.strip()
    for case in load_dataset().cases:
        if case.input == normalized_input:
            return run_fixture(case, profile)
    return FixtureResponse(
        answer="I do not have enough approved evidence to answer that request.",
        retrieved_document_ids=(),
        citations=(),
        refused=True,
        profile=profile,
    )
