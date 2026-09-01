from __future__ import annotations

import json

import pytest

from aqe.stucktoship import (
    StuckToShipClient,
    StuckToShipTargetError,
    load_stucktoship_dataset,
)


def _success_payload(*, trace: dict | None = None) -> str:
    return json.dumps(
        {
            "code": 0,
            "data": {
                "answer": "RAG combines retrieval with generation.",
                "references": [
                    {
                        "source_path": "knowledge/courses/rag-basics.md",
                        "score": 6.0,
                    },
                ],
                "route": "course",
                "trace": trace if trace is not None else {"decision": "accept"},
            },
        },
    )


def test_client_normalizes_successful_stucktoship_response_without_changing_reference_identity():
    received: dict[str, object] = {}

    def transport(url, payload, headers, timeout_seconds):
        received.update(
            url=url,
            payload=payload,
            headers=headers,
            timeout_seconds=timeout_seconds,
        )
        return 200, _success_payload()

    case = load_stucktoship_dataset().cases[0]
    client = StuckToShipClient(
        base_url="http://127.0.0.1:8010/",
        api_key="secret-for-test-only",
        transport=transport,
    )

    response = client.ask(case)

    assert received["url"] == "http://127.0.0.1:8010/api/v1/rag/ask"
    assert received["payload"] == {
        "query": case.query,
        "stream": False,
        "session_id": f"aqe-stucktoship-{case.id}",
    }
    assert received["headers"] == {"Authorization": "Bearer secret-for-test-only"}
    assert response.answer == "RAG combines retrieval with generation."
    assert response.reference_ids == ("knowledge/courses/rag-basics.md",)
    assert response.route == "course"
    assert response.trace == {"decision": "accept"}
    assert "secret-for-test-only" not in response.to_dict().__repr__()


def test_client_rejects_incomplete_target_contract_without_leaking_api_key():
    def transport(url, payload, headers, timeout_seconds):
        return 200, _success_payload(trace=None).replace(', "trace": {"decision": "accept"}', "")

    case = load_stucktoship_dataset().cases[0]
    client = StuckToShipClient(
        base_url="http://127.0.0.1:8010",
        api_key="do-not-leak-this-key",
        transport=transport,
    )

    with pytest.raises(StuckToShipTargetError, match="trace") as error:
        client.ask(case)

    assert "do-not-leak-this-key" not in str(error.value)


def test_stucktoship_corpus_spans_course_code_faq_and_clarify_routes():
    dataset = load_stucktoship_dataset()

    assert dataset.version == "stucktoship-rag-v1"
    assert {case.expected_route for case in dataset.cases} == {
        "course",
        "code",
        "faq",
        "clarify",
    }
