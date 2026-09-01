from __future__ import annotations

import json


def test_redact_for_evidence_sanitizes_nested_secrets_and_local_paths():
    from aqe.redaction import redact_for_evidence

    payload = {
        "trace": {
            "authorization": "Bearer live-token-123",
            "nested": {"api_key": "key-123", "message": "manual-secret at D:\\Users\\alice\\repo\\main.py"},
        }
    }

    result = redact_for_evidence(payload, secrets=("manual-secret",))

    serialized = json.dumps(result)
    assert "live-token-123" not in serialized
    assert "key-123" not in serialized
    assert "manual-secret" not in serialized
    assert "D:\\Users\\alice" not in serialized
    assert result["trace"]["nested"]["message"].endswith("[LOCAL_PATH]/main.py")


def test_evidence_store_writes_redacted_content_with_stable_identifier(tmp_path):
    from aqe.evidence_store import EvidenceStore

    store = EvidenceStore(tmp_path)
    artifact = store.persist(
        {
            "verdict": "block",
            "trace": {"token": "not-for-disk", "source_path": "D:\\Users\\alice\\repo\\main.py"},
        }
    )

    assert artifact.path.name == f"{artifact.evidence_id}.json"
    document = json.loads(artifact.path.read_text(encoding="utf-8"))
    assert document["schema_version"] == "aqe-evidence-v1"
    assert document["evidence_id"] == artifact.evidence_id
    assert document["evidence"]["trace"]["token"] == "[REDACTED]"
    assert document["evidence"]["trace"]["source_path"] == "[LOCAL_PATH]/main.py"
