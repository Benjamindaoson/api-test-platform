from __future__ import annotations

from aqe.models import EvidencePackage


def _redact(value: str, markers: tuple[str, ...]) -> str:
    redacted_value = value
    for marker in markers:
        redacted_value = redacted_value.replace(marker, "[REDACTED_PROTECTED_MARKER]")
    return redacted_value


def public_evidence(evidence: EvidencePackage) -> dict:
    """Serialize evidence for HTTP without returning protected marker values."""
    return {
        "dataset_version": evidence.dataset_version,
        "profile": evidence.profile,
        "verdict": evidence.verdict,
        "reasons": list(evidence.reasons),
        "case_results": [
            {
                "case_id": result.case_id,
                "severity": result.severity,
                "passed": result.passed,
                "findings": [
                    {"rule_id": finding.rule_id, "message": finding.message}
                    for finding in result.findings
                ],
                "response": {
                    "answer": _redact(result.response.answer, result.redaction_markers),
                    "retrieved_document_ids": list(result.response.retrieved_document_ids),
                    "citations": list(result.response.citations),
                    "refused": result.response.refused,
                    "profile": result.response.profile,
                },
            }
            for result in evidence.case_results
        ],
    }
