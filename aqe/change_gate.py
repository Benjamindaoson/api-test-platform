from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Callable, Collection

from aqe.evidence_store import EvidenceStore
from aqe.redaction import redact_for_evidence
from aqe.stucktoship import DEFAULT_STUCKTOSHIP_BASE_URL, StuckToShipClient, local_stucktoship_config
from aqe.stucktoship_gate import StuckToShipAnswerer, StuckToShipEvidence, run_stucktoship_gate


ClientFactory = Callable[..., StuckToShipAnswerer]
_CODE_SUFFIXES = {".py", ".pyi", ".js", ".jsx", ".ts", ".tsx", ".go", ".java", ".rs"}


@dataclass(frozen=True)
class ChangeGateResult:
    verdict: str
    changed_files: tuple[str, ...]
    categories: tuple[str, ...]
    reasons: tuple[str, ...]
    evidence: StuckToShipEvidence | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "verdict": self.verdict,
            "changed_files": list(self.changed_files),
            "categories": list(self.categories),
            "reasons": list(self.reasons),
            "evidence": self.evidence.to_dict() if self.evidence else None,
        }


def classify_changed_files(changed_files: Collection[str]) -> tuple[str, ...]:
    categories: set[str] = set()
    for changed_file in changed_files:
        path = PurePosixPath(changed_file.replace("\\", "/").lower())
        parts = path.parts
        text = "/".join(parts)
        if path.suffix in _CODE_SUFFIXES or path.name in {"dockerfile", "docker-compose.yml", "docker-compose.yaml"}:
            categories.add("code")
        if any(part in {"prompt", "prompts", "template", "templates"} for part in parts) or "system_prompt" in text:
            categories.add("prompt")
        if (
            any(part in {"knowledge", "corpus", "index", "indexes", "fixtures"} for part in parts)
            or path.suffix == ".jsonl"
            or (path.suffix in {".md", ".json", ".yaml", ".yml"} and any(token in text for token in ("retrieval", "embedding", "chunk", "index")))
        ):
            categories.add("knowledge_index")
    return tuple(sorted(categories))


def run_change_gate(
    changed_files: Collection[str],
    *,
    client: StuckToShipAnswerer,
) -> ChangeGateResult:
    files = tuple(dict.fromkeys(path.replace("\\", "/") for path in changed_files if path))
    categories = classify_changed_files(files)
    if not categories:
        return ChangeGateResult(
            verdict="not_applicable",
            changed_files=files,
            categories=(),
            reasons=("No AQE-relevant code, Prompt, or knowledge/index change was detected.",),
        )
    evidence = run_stucktoship_gate(client=client)
    return ChangeGateResult(
        verdict=evidence.verdict,
        changed_files=files,
        categories=categories,
        reasons=evidence.reasons,
        evidence=evidence,
    )


def git_changed_files(base_ref: str) -> tuple[str, ...]:
    result = subprocess.run(
        ["git", "diff", "--name-only", f"{base_ref}...HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    return tuple(line for line in result.stdout.splitlines() if line)


def main(
    argv: list[str] | None = None,
    *,
    client_factory: ClientFactory = StuckToShipClient,
) -> int:
    parser = argparse.ArgumentParser(description="Run the AQE target gate only for relevant repository changes.")
    parser.add_argument("--changed-file", action="append", default=[], help="Changed path; repeat in CI.")
    parser.add_argument("--base-ref", default="HEAD~1", help="Git base ref when changed paths are omitted.")
    parser.add_argument("--base-url", default=None, help="StuckToShip HTTP origin")
    parser.add_argument("--evidence-dir", default=None, help="Optional directory for a redacted AQE evidence bundle.")
    args = parser.parse_args(argv)
    try:
        files = tuple(args.changed_file) if args.changed_file else git_changed_files(args.base_ref)
    except (OSError, subprocess.CalledProcessError) as error:
        failure = ChangeGateResult(
            verdict="escalate",
            changed_files=(),
            categories=(),
            reasons=(f"Unable to determine changed files: {error.__class__.__name__}.",),
        )
        print(json.dumps(failure.to_dict(), ensure_ascii=False))
        return 2
    configured_url, api_key = local_stucktoship_config()
    client = client_factory(
        base_url=args.base_url or configured_url or DEFAULT_STUCKTOSHIP_BASE_URL,
        api_key=api_key,
    )
    gate = run_change_gate(files, client=client)
    serialized = redact_for_evidence(gate.to_dict(), secrets=(api_key or "",))
    if args.evidence_dir and gate.evidence is not None:
        artifact = EvidenceStore(args.evidence_dir, secrets=(api_key or "",)).persist(gate.to_dict())
        serialized["evidence_artifact"] = {"evidence_id": artifact.evidence_id, "file_name": artifact.path.name}
    print(json.dumps(serialized, ensure_ascii=False))
    return {"pass": 0, "block": 1, "escalate": 2, "not_applicable": 0}[gate.verdict]


if __name__ == "__main__":
    raise SystemExit(main())
