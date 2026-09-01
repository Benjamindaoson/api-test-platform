from __future__ import annotations

from aqe.evidence_store import EvidenceStore
from aqe.stucktoship import StuckToShipResponse, load_stucktoship_dataset


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


def test_replay_runs_only_cases_recorded_in_compatible_evidence(tmp_path):
    from aqe.incident_replay import replay_evidence

    dataset = load_stucktoship_dataset()
    artifact = EvidenceStore(tmp_path).persist(
        {
            "dataset_version": dataset.version,
            "case_results": [{"case_id": "code-create-app"}],
        }
    )
    client = RecordingClient()

    replay = replay_evidence(artifact.path, client=client)

    assert replay.verdict == "pass"
    assert replay.replayed_case_ids == ("code-create-app",)
    assert client.case_ids == ["code-create-app"]


def test_replay_escalates_before_contacting_target_when_dataset_mismatches(tmp_path):
    from aqe.incident_replay import replay_evidence

    artifact = EvidenceStore(tmp_path).persist(
        {"dataset_version": "retired-dataset-v0", "case_results": [{"case_id": "code-create-app"}]}
    )
    client = RecordingClient()

    replay = replay_evidence(artifact.path, client=client)

    assert replay.verdict == "escalate"
    assert client.case_ids == []
    assert "dataset version" in replay.reasons[0].lower()
