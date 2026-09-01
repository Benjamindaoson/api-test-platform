from __future__ import annotations


def test_audit_ledger_enforces_local_role_policy_and_chains_events(tmp_path):
    from aqe.audit import AuditLedger, AuditPermissionError

    ledger = AuditLedger(tmp_path / "audit.jsonl")
    first = ledger.append(actor_role="operator", action="persist", metadata={"verdict": "pass"})
    second = ledger.append(actor_role="system", action="replay", metadata={"verdict": "block"})

    assert second.previous_digest == first.digest
    assert len(ledger.read(actor_role="auditor")) == 2
    try:
        ledger.append(actor_role="viewer", action="persist", metadata={})
    except AuditPermissionError:
        pass
    else:
        raise AssertionError("viewer write must be rejected")


def test_trends_only_use_metadata_and_compute_block_rate():
    from aqe.audit import AuditEvent, summarize_trends

    summary = summarize_trends(
        [
            AuditEvent("1", "", "operator", "persist", {"verdict": "pass"}),
            AuditEvent("2", "1", "operator", "persist", {"verdict": "block"}),
            AuditEvent("3", "2", "operator", "persist", {"verdict": "escalate"}),
        ]
    )

    assert summary.verdict_counts == {"pass": 1, "block": 1, "escalate": 1}
    assert summary.block_rate == 0.5
