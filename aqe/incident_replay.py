from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from aqe.evidence_store import EvidenceStore, load_evidence
from aqe.redaction import redact_for_evidence
from aqe.stucktoship import DEFAULT_STUCKTOSHIP_BASE_URL, StuckToShipClient, local_stucktoship_config
from aqe.stucktoship_gate import StuckToShipAnswerer, StuckToShipEvidence, run_stucktoship_gate


@dataclass(frozen=True)
class IncidentReplay:
    source_evidence_id: str
    replayed_case_ids: tuple[str, ...]
    evidence: StuckToShipEvidence

    @property
    def verdict(self) -> str:
        return self.evidence.verdict

    @property
    def reasons(self) -> tuple[str, ...]:
        return self.evidence.reasons

    def to_dict(self) -> dict[str, object]:
        return {
            "source_evidence_id": self.source_evidence_id,
            "replayed_case_ids": list(self.replayed_case_ids),
            "evidence": self.evidence.to_dict(),
        }


def replay_evidence(path: str | Path, *, client: StuckToShipAnswerer) -> IncidentReplay:
    document = load_evidence(path)
    source_evidence_id = document["evidence_id"]
    recorded = document["evidence"]
    from aqe.stucktoship import load_stucktoship_dataset

    dataset = load_stucktoship_dataset()
    if recorded.get("dataset_version") != dataset.version:
        return IncidentReplay(
            source_evidence_id=source_evidence_id,
            replayed_case_ids=(),
            evidence=_escalated_replay_evidence(
                dataset.version,
                "Evidence dataset version is incompatible with the installed target corpus.",
            ),
        )
    case_ids = _recorded_case_ids(recorded)
    if not case_ids:
        return IncidentReplay(
            source_evidence_id=source_evidence_id,
            replayed_case_ids=(),
            evidence=_escalated_replay_evidence(dataset.version, "Evidence bundle recorded no replayable cases."),
        )
    evidence = run_stucktoship_gate(client=client, case_ids=case_ids)
    return IncidentReplay(
        source_evidence_id=source_evidence_id,
        replayed_case_ids=case_ids,
        evidence=evidence,
    )


def _recorded_case_ids(evidence: dict) -> tuple[str, ...]:
    results = evidence.get("case_results")
    if not isinstance(results, list):
        return ()
    ids: list[str] = []
    for result in results:
        if not isinstance(result, dict) or not isinstance(result.get("case_id"), str):
            return ()
        if result["case_id"] not in ids:
            ids.append(result["case_id"])
    return tuple(ids)


def _escalated_replay_evidence(dataset_version: str, reason: str) -> StuckToShipEvidence:
    return StuckToShipEvidence(
        dataset_version=dataset_version,
        target="stucktoship-http",
        verdict="escalate",
        reasons=(reason,),
        case_results=(),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Replay AQE cases recorded in a redacted evidence bundle.")
    parser.add_argument("--evidence", required=True, help="Path to an AQE evidence JSON bundle.")
    parser.add_argument("--base-url", default=None, help="StuckToShip HTTP origin")
    parser.add_argument("--evidence-dir", default=None, help="Optional directory for replay evidence.")
    args = parser.parse_args(argv)
    configured_url, api_key = local_stucktoship_config()
    client = StuckToShipClient(
        base_url=args.base_url or configured_url or DEFAULT_STUCKTOSHIP_BASE_URL,
        api_key=api_key,
    )
    replay = replay_evidence(args.evidence, client=client)
    serialized = redact_for_evidence(replay.to_dict(), secrets=(api_key or "",))
    if args.evidence_dir:
        artifact = EvidenceStore(args.evidence_dir, secrets=(api_key or "",)).persist(serialized)
        serialized["evidence_artifact"] = {"evidence_id": artifact.evidence_id, "file_name": artifact.path.name}
    print(json.dumps(serialized, ensure_ascii=False))
    return {"pass": 0, "block": 1, "escalate": 2}[replay.verdict]


if __name__ == "__main__":
    raise SystemExit(main())
