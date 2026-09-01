from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


_PATH = Path(__file__).with_name("fixtures") / "historical_incidents_v1.json"


@dataclass(frozen=True)
class HistoricalIncident:
    id: str
    expected_answer_fragments: tuple[str, ...]
    fixed_revision: str


@dataclass(frozen=True)
class HistoricalIncidentCorpus:
    version: str
    incidents: tuple[HistoricalIncident, ...]


@dataclass(frozen=True)
class IncidentRegressionResult:
    incident_id: str
    verdict: str
    missing_fragments: tuple[str, ...]


def load_historical_incidents() -> HistoricalIncidentCorpus:
    payload = json.loads(_PATH.read_text(encoding="utf-8"))
    incidents = tuple(
        HistoricalIncident(
            id=str(item["id"]),
            expected_answer_fragments=tuple(item["expected_answer_fragments"]),
            fixed_revision=str(item["fixed_revision"]),
        )
        for item in payload["incidents"]
    )
    if not payload.get("version") or not incidents:
        raise ValueError("Invalid historical incident corpus.")
    return HistoricalIncidentCorpus(str(payload["version"]), incidents)


def evaluate_incident_response(incident: HistoricalIncident, answer: str) -> IncidentRegressionResult:
    missing = tuple(
        fragment for fragment in incident.expected_answer_fragments if fragment.lower() not in answer.lower()
    )
    return IncidentRegressionResult(
        incident_id=incident.id,
        verdict="block" if missing else "pass",
        missing_fragments=missing,
    )
