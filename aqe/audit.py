from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping, Sequence

from aqe.redaction import redact_for_evidence


class AuditPermissionError(PermissionError):
    pass


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    previous_digest: str
    actor_role: str
    action: str
    metadata: Mapping[str, object]
    digest: str = ""


@dataclass(frozen=True)
class TrendSummary:
    verdict_counts: dict[str, int]
    block_rate: float


class AuditLedger:
    _WRITE_ROLES = {"system", "operator"}
    _READ_ROLES = {"system", "operator", "auditor", "viewer"}

    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, *, actor_role: str, action: str, metadata: Mapping[str, object]) -> AuditEvent:
        if actor_role not in self._WRITE_ROLES:
            raise AuditPermissionError(f"Role '{actor_role}' cannot append audit events.")
        existing = self.read(actor_role="system")
        previous = existing[-1].digest if existing else ""
        sanitized = redact_for_evidence(dict(metadata))
        event_id = hashlib.sha256(json.dumps(sanitized, sort_keys=True).encode()).hexdigest()[:16]
        unsigned = AuditEvent(event_id, previous, actor_role, action, sanitized)
        digest = hashlib.sha256(json.dumps(asdict(unsigned), sort_keys=True).encode()).hexdigest()
        event = AuditEvent(event_id, previous, actor_role, action, sanitized, digest)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as output:
            output.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True) + "\n")
        return event

    def read(self, *, actor_role: str) -> list[AuditEvent]:
        if actor_role not in self._READ_ROLES:
            raise AuditPermissionError(f"Role '{actor_role}' cannot read audit events.")
        if not self.path.exists():
            return []
        return [AuditEvent(**json.loads(line)) for line in self.path.read_text(encoding="utf-8").splitlines() if line]


def summarize_trends(events: Sequence[AuditEvent]) -> TrendSummary:
    counts = {"pass": 0, "block": 0, "escalate": 0}
    for event in events:
        verdict = event.metadata.get("verdict")
        if verdict in counts:
            counts[verdict] += 1
    terminal = counts["pass"] + counts["block"]
    return TrendSummary(counts, counts["block"] / terminal if terminal else 0.0)
