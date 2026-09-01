from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aqe.redaction import redact_for_evidence


SCHEMA_VERSION = "aqe-evidence-v1"


@dataclass(frozen=True)
class EvidenceArtifact:
    evidence_id: str
    path: Path


class EvidenceStore:
    """Local, JSON-only evidence store for unattended AQE runs."""

    def __init__(self, directory: str | Path, *, secrets: tuple[str, ...] = ()):
        self.directory = Path(directory)
        self.secrets = secrets

    def persist(self, evidence: dict[str, Any]) -> EvidenceArtifact:
        sanitized = redact_for_evidence(evidence, secrets=self.secrets)
        canonical = json.dumps(sanitized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        evidence_id = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
        document = {
            "schema_version": SCHEMA_VERSION,
            "evidence_id": evidence_id,
            "evidence": sanitized,
        }
        self.directory.mkdir(parents=True, exist_ok=True)
        path = self.directory / f"{evidence_id}.json"
        _atomic_json_write(path, document)
        return EvidenceArtifact(evidence_id=evidence_id, path=path)


def load_evidence(path: str | Path) -> dict[str, Any]:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if document.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Unsupported AQE evidence schema.")
    if not isinstance(document.get("evidence_id"), str) or not isinstance(document.get("evidence"), dict):
        raise ValueError("Invalid AQE evidence bundle.")
    return document


def _atomic_json_write(path: Path, document: dict[str, Any]) -> None:
    handle = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.stem}.",
        suffix=".tmp",
        delete=False,
    )
    try:
        with handle:
            json.dump(document, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(handle.name, path)
    finally:
        if os.path.exists(handle.name):
            os.unlink(handle.name)
