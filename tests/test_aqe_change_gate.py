from __future__ import annotations

from aqe.stucktoship import StuckToShipResponse


class RecordingClient:
    def __init__(self):
        self.case_ids: list[str] = []

    def ask(self, case):
        self.case_ids.append(case.id)
        return StuckToShipResponse(
            answer=" ".join(case.required_answer_fragments) or "Grounded target answer.",
            reference_ids=("knowledge/source.md",) if case.citation_required else (),
            route=case.expected_route,
            trace={"decision": "clarify" if case.requires_clarification else "accept"},
        )


def test_change_gate_runs_real_target_gate_for_prompt_code_and_knowledge_changes():
    from aqe.change_gate import run_change_gate

    client = RecordingClient()
    result = run_change_gate(
        ["prompts/system_answer.md", "core/retrieval.py", "knowledge/courses/rag.md"],
        client=client,
    )

    assert result.verdict == "pass"
    assert result.categories == ("code", "knowledge_index", "prompt")
    assert result.evidence is not None
    assert len(client.case_ids) == 4


def test_change_gate_marks_unrelated_changes_not_applicable_without_contacting_target():
    from aqe.change_gate import run_change_gate

    client = RecordingClient()
    result = run_change_gate(["docs/contributing.md", ".github/ISSUE_TEMPLATE/bug.md"], client=client)

    assert result.verdict == "not_applicable"
    assert result.evidence is None
    assert client.case_ids == []
