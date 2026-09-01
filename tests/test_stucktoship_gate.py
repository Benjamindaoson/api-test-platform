from __future__ import annotations

import json
from dataclasses import replace

from aqe.stucktoship import (
    StuckToShipResponse,
    StuckToShipTargetError,
    load_stucktoship_dataset,
)
from aqe.stucktoship_gate import main, run_stucktoship_gate


class PlannedClient:
    def __init__(self, responses: dict[str, StuckToShipResponse]):
        self.responses = responses

    def ask(self, case):
        return self.responses[case.id]


class UnreachableClient:
    def ask(self, case):
        raise StuckToShipTargetError("Target request failed: connection unavailable")


def _passing_responses() -> dict[str, StuckToShipResponse]:
    responses = {}
    for case in load_stucktoship_dataset().cases:
        responses[case.id] = StuckToShipResponse(
            answer=" ".join(case.required_answer_fragments) or "Grounded target answer.",
            reference_ids=(f"knowledge/{case.id}.md",) if case.citation_required else (),
            route=case.expected_route,
            trace={"decision": "clarify" if case.requires_clarification else "accept"},
        )
    return responses


def test_missing_citation_blocks_an_answerable_target_case():
    responses = _passing_responses()
    course_case = next(
        case for case in load_stucktoship_dataset().cases if case.expected_route == "course"
    )
    responses[course_case.id] = replace(responses[course_case.id], reference_ids=())

    evidence = run_stucktoship_gate(client=PlannedClient(responses))

    assert evidence.verdict == "block"
    assert "citation-presence" in evidence.rule_ids


def test_wrong_symbol_answer_blocks_even_when_route_and_citation_exist():
    responses = _passing_responses()
    code_case = next(
        case for case in load_stucktoship_dataset().cases if case.expected_route == "code"
    )
    responses[code_case.id] = replace(
        responses[code_case.id],
        answer="create is in core/stream_queue.py:14.",
    )

    evidence = run_stucktoship_gate(client=PlannedClient(responses))

    assert evidence.verdict == "block"
    assert "answer-correctness" in evidence.rule_ids


def test_unreachable_target_escalates_instead_of_passing_or_blocking():
    evidence = run_stucktoship_gate(client=UnreachableClient())

    assert evidence.verdict == "escalate"
    assert evidence.case_results == ()
    assert "connection unavailable" in evidence.reasons[0]


def test_cli_defaults_to_local_edurag_url_and_emits_json_evidence(monkeypatch, capsys):
    monkeypatch.delenv("AQE_STUCKTOSHIP_BASE_URL", raising=False)
    captured: dict[str, str] = {}
    responses = _passing_responses()

    def client_factory(*, base_url: str, api_key: str | None):
        captured["base_url"] = base_url
        captured["api_key"] = api_key or ""
        return PlannedClient(responses)

    exit_code = main([], client_factory=client_factory)

    assert exit_code == 0
    assert captured == {"base_url": "http://127.0.0.1:8010", "api_key": ""}
    assert '"verdict": "pass"' in capsys.readouterr().out


def test_cli_persists_sanitized_evidence_bundle(tmp_path, capsys):
    responses = _passing_responses()
    course_case = next(case for case in load_stucktoship_dataset().cases if case.expected_route == "course")
    responses[course_case.id] = replace(
        responses[course_case.id],
        trace={"token": "not-for-evidence", "source_path": "D:\\Users\\alice\\repo\\main.py"},
    )

    exit_code = main(
        ["--evidence-dir", str(tmp_path)],
        client_factory=lambda **_kwargs: PlannedClient(responses),
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "not-for-evidence" not in output
    assert "D:\\Users\\alice" not in output
    artifact = next(tmp_path.glob("*.json"))
    saved = json.loads(artifact.read_text(encoding="utf-8"))
    assert saved["evidence"]["case_results"][0]["response"]["trace"]["token"] == "[REDACTED]"
