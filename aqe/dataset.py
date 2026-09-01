from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from aqe.models import EvaluationCase, EvaluationDataset


_DATASET_PATH = Path(__file__).parent / "fixtures" / "rag_release_gate_v1.json"
_ALLOWED_SEVERITIES = {"critical", "high", "medium", "low"}


def _as_tuple(value: Any, field_name: str, case_id: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"Case '{case_id}' field '{field_name}' must be a list of strings")
    return tuple(value)


def _load_case(raw_case: Any) -> EvaluationCase:
    if not isinstance(raw_case, dict):
        raise ValueError("Every dataset case must be an object")

    case_id = raw_case.get("id")
    input_text = raw_case.get("input")
    severity = raw_case.get("severity")
    response = raw_case.get("baseline_response")
    if not isinstance(case_id, str) or not case_id:
        raise ValueError("Every dataset case requires a non-empty id")
    if not isinstance(input_text, str) or not input_text:
        raise ValueError(f"Case '{case_id}' requires a non-empty input")
    if severity not in _ALLOWED_SEVERITIES:
        raise ValueError(f"Case '{case_id}' has an unsupported severity")
    if not isinstance(response, dict):
        raise ValueError(f"Case '{case_id}' requires a baseline_response object")

    answer = response.get("answer")
    refused = response.get("refused")
    if not isinstance(answer, str) or not isinstance(refused, bool):
        raise ValueError(f"Case '{case_id}' has an invalid baseline response")

    expected_answer = raw_case.get("expected_answer_fragment")
    if not isinstance(expected_answer, str):
        raise ValueError(f"Case '{case_id}' expected_answer_fragment must be a string")
    expects_refusal = raw_case.get("expects_refusal")
    if not isinstance(expects_refusal, bool):
        raise ValueError(f"Case '{case_id}' expects_refusal must be a boolean")
    if not expects_refusal and not expected_answer:
        raise ValueError(
            f"Case '{case_id}' requires a non-empty expected_answer_fragment when refusal is not expected",
        )

    return EvaluationCase(
        id=case_id,
        input=input_text,
        severity=severity,
        expected_answer_fragment=expected_answer,
        expected_citations=_as_tuple(raw_case.get("expected_citations", []), "expected_citations", case_id),
        expects_refusal=expects_refusal,
        protected_markers=_as_tuple(raw_case.get("protected_markers", []), "protected_markers", case_id),
        baseline_answer=answer,
        baseline_retrieved_document_ids=_as_tuple(
            response.get("retrieved_document_ids", []), "baseline_response.retrieved_document_ids", case_id,
        ),
        baseline_citations=_as_tuple(response.get("citations", []), "baseline_response.citations", case_id),
        baseline_refused=refused,
        alternate_document_id=raw_case.get("alternate_document_id", ""),
    )


@lru_cache(maxsize=1)
def load_dataset() -> EvaluationDataset:
    """Load the checked-in fixture dataset and reject malformed release inputs."""
    with _DATASET_PATH.open(encoding="utf-8") as dataset_file:
        raw_dataset = json.load(dataset_file)

    if not isinstance(raw_dataset, dict):
        raise ValueError("Dataset must be a JSON object")
    version = raw_dataset.get("version")
    raw_cases = raw_dataset.get("cases")
    if not isinstance(version, str) or not version:
        raise ValueError("Dataset requires a non-empty version")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("Dataset requires at least one case")

    cases = tuple(_load_case(raw_case) for raw_case in raw_cases)
    ids = [case.id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Dataset case ids must be unique")
    return EvaluationDataset(version=version, cases=cases)
