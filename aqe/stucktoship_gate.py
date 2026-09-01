from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Callable, Collection, Protocol

from aqe.evidence_store import EvidenceStore
from aqe.redaction import redact_for_evidence
from aqe.stucktoship import (
    DEFAULT_STUCKTOSHIP_BASE_URL,
    StuckToShipCase,
    StuckToShipClient,
    StuckToShipResponse,
    StuckToShipTargetError,
    load_stucktoship_dataset,
    local_stucktoship_config,
)


class StuckToShipAnswerer(Protocol):
    def ask(self, case: StuckToShipCase) -> StuckToShipResponse: ...


ClientFactory = Callable[..., StuckToShipAnswerer]


@dataclass(frozen=True)
class StuckToShipFinding:
    rule_id: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"rule_id": self.rule_id, "message": self.message}


@dataclass(frozen=True)
class StuckToShipCaseResult:
    case_id: str
    passed: bool
    findings: tuple[StuckToShipFinding, ...]
    response: StuckToShipResponse

    def to_dict(self) -> dict[str, object]:
        return {
            "case_id": self.case_id,
            "passed": self.passed,
            "findings": [finding.to_dict() for finding in self.findings],
            "response": self.response.to_dict(),
        }


@dataclass(frozen=True)
class StuckToShipEvidence:
    dataset_version: str
    target: str
    verdict: str
    reasons: tuple[str, ...]
    case_results: tuple[StuckToShipCaseResult, ...]

    @property
    def rule_ids(self) -> tuple[str, ...]:
        return tuple(
            finding.rule_id
            for result in self.case_results
            for finding in result.findings
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "dataset_version": self.dataset_version,
            "target": self.target,
            "verdict": self.verdict,
            "reasons": list(self.reasons),
            "case_results": [result.to_dict() for result in self.case_results],
        }


def run_stucktoship_gate(
    *,
    client: StuckToShipAnswerer | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
    case_ids: Collection[str] | None = None,
) -> StuckToShipEvidence:
    dataset = load_stucktoship_dataset()
    selected_cases = dataset.cases
    if case_ids is not None:
        requested = tuple(dict.fromkeys(case_ids))
        available = {case.id: case for case in dataset.cases}
        missing = tuple(case_id for case_id in requested if case_id not in available)
        if missing:
            return StuckToShipEvidence(
                dataset_version=dataset.version,
                target="stucktoship-http",
                verdict="escalate",
                reasons=(f"Requested evaluation cases are unavailable: {', '.join(missing)}.",),
                case_results=(),
            )
        if not requested:
            return StuckToShipEvidence(
                dataset_version=dataset.version,
                target="stucktoship-http",
                verdict="escalate",
                reasons=("No evaluation cases were requested for target replay.",),
                case_results=(),
            )
        selected_cases = tuple(available[case_id] for case_id in requested)
    if client is None:
        configured_url, configured_key = local_stucktoship_config()
        client = StuckToShipClient(
            base_url=base_url or configured_url,
            api_key=api_key if api_key is not None else configured_key,
        )

    case_results: list[StuckToShipCaseResult] = []
    for case in selected_cases:
        try:
            response = client.ask(case)
        except StuckToShipTargetError as error:
            return StuckToShipEvidence(
                dataset_version=dataset.version,
                target="stucktoship-http",
                verdict="escalate",
                reasons=(str(error),),
                case_results=(),
            )
        case_results.append(_evaluate_case(case, response))

    failed = [result for result in case_results if not result.passed]
    if failed:
        reasons = tuple(
            f"Case '{result.case_id}' failed rules: {', '.join(finding.rule_id for finding in result.findings)}."
            for result in failed
        )
        return StuckToShipEvidence(
            dataset_version=dataset.version,
            target="stucktoship-http",
            verdict="block",
            reasons=reasons,
            case_results=tuple(case_results),
        )
    return StuckToShipEvidence(
        dataset_version=dataset.version,
        target="stucktoship-http",
        verdict="pass",
        reasons=("All StuckToShip target cases passed.",),
        case_results=tuple(case_results),
    )


def _evaluate_case(
    case: StuckToShipCase,
    response: StuckToShipResponse,
) -> StuckToShipCaseResult:
    findings: list[StuckToShipFinding] = []
    if response.route != case.expected_route:
        findings.append(
            StuckToShipFinding("route", f"Expected route '{case.expected_route}', got '{response.route}'."),
        )
    if case.citation_required and not response.reference_ids:
        findings.append(
            StuckToShipFinding("citation-presence", "Answerable response did not include a reference."),
        )
    missing_fragments = [
        fragment
        for fragment in case.required_answer_fragments
        if fragment.lower() not in response.answer.lower()
    ]
    if missing_fragments:
        findings.append(
            StuckToShipFinding(
                "answer-correctness",
                f"Response omitted required answer fragments: {', '.join(missing_fragments)}.",
            ),
        )
    if case.requires_clarification and response.trace.get("decision") != "clarify":
        findings.append(
            StuckToShipFinding("clarification", "Clarify case did not report a clarify trace decision."),
        )
    return StuckToShipCaseResult(
        case_id=case.id,
        passed=not findings,
        findings=tuple(findings),
        response=response,
    )


def main(
    argv: list[str] | None = None,
    *,
    client_factory: ClientFactory = StuckToShipClient,
) -> int:
    parser = argparse.ArgumentParser(description="Run AQE against the local StuckToShip RAG target.")
    parser.add_argument("--base-url", default=None, help="StuckToShip HTTP origin")
    parser.add_argument(
        "--evidence-dir",
        default=None,
        help="Optional directory for a redacted AQE evidence bundle.",
    )
    args = parser.parse_args(argv)
    configured_url, api_key = local_stucktoship_config()
    base_url = args.base_url or configured_url or DEFAULT_STUCKTOSHIP_BASE_URL
    client = client_factory(base_url=base_url, api_key=api_key)
    evidence = run_stucktoship_gate(client=client)
    serialized = redact_for_evidence(evidence.to_dict(), secrets=(api_key or "",))
    if args.evidence_dir:
        artifact = EvidenceStore(args.evidence_dir, secrets=(api_key or "",)).persist(evidence.to_dict())
        serialized["evidence_artifact"] = {
            "evidence_id": artifact.evidence_id,
            "file_name": artifact.path.name,
        }
    print(json.dumps(serialized, ensure_ascii=False))
    return {"pass": 0, "block": 1, "escalate": 2}[evidence.verdict]


if __name__ == "__main__":
    raise SystemExit(main())
