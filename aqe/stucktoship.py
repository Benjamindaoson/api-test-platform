from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


_DATASET_PATH = Path(__file__).with_name("fixtures") / "stucktoship_rag_v1.json"
DEFAULT_STUCKTOSHIP_BASE_URL = "http://127.0.0.1:8010"
Transport = Callable[[str, dict[str, object], dict[str, str], float], tuple[int, str]]


class StuckToShipTargetError(RuntimeError):
    """A safe description of a target availability or contract failure."""


@dataclass(frozen=True)
class StuckToShipCase:
    id: str
    query: str
    expected_route: str
    citation_required: bool
    requires_clarification: bool
    required_answer_fragments: tuple[str, ...]


@dataclass(frozen=True)
class StuckToShipDataset:
    version: str
    cases: tuple[StuckToShipCase, ...]


@dataclass(frozen=True)
class StuckToShipResponse:
    answer: str
    reference_ids: tuple[str, ...]
    route: str
    trace: dict[str, Any]

    def to_dict(self) -> dict[str, object]:
        return {
            "answer": self.answer,
            "reference_ids": list(self.reference_ids),
            "route": self.route,
            "trace": self.trace,
        }


def load_stucktoship_dataset(path: Path | None = None) -> StuckToShipDataset:
    raw = json.loads((path or _DATASET_PATH).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not isinstance(raw.get("version"), str):
        raise ValueError("StuckToShip dataset must contain a string version.")
    raw_cases = raw.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("StuckToShip dataset must contain executable cases.")

    cases: list[StuckToShipCase] = []
    for item in raw_cases:
        if not isinstance(item, dict):
            raise ValueError("StuckToShip dataset cases must be objects.")
        try:
            case = StuckToShipCase(
                id=_required_string(item, "id"),
                query=_required_string(item, "query"),
                expected_route=_required_string(item, "expected_route"),
                citation_required=_required_bool(item, "citation_required"),
                requires_clarification=_required_bool(item, "requires_clarification"),
                required_answer_fragments=_required_strings(item, "required_answer_fragments"),
            )
        except ValueError as error:
            raise ValueError(f"Invalid StuckToShip dataset case: {error}") from error
        cases.append(case)
    return StuckToShipDataset(version=raw["version"], cases=tuple(cases))


class StuckToShipClient:
    def __init__(
        self,
        *,
        base_url: str = DEFAULT_STUCKTOSHIP_BASE_URL,
        api_key: str | None = None,
        timeout_seconds: float = 20.0,
        transport: Transport | None = None,
    ) -> None:
        self.base_url = _normalize_base_url(base_url)
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self._transport = transport or _urllib_transport

    def ask(self, case: StuckToShipCase) -> StuckToShipResponse:
        payload: dict[str, object] = {
            "query": case.query,
            "stream": False,
            "session_id": f"aqe-stucktoship-{case.id}",
        }
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            status, raw = self._transport(
                f"{self.base_url}/api/v1/rag/ask",
                payload,
                headers,
                self.timeout_seconds,
            )
        except StuckToShipTargetError:
            raise
        except Exception as error:
            raise StuckToShipTargetError("Target request failed: network unavailable.") from error
        return _parse_target_response(status, raw)


def local_stucktoship_config() -> tuple[str, str | None]:
    return (
        os.getenv("AQE_STUCKTOSHIP_BASE_URL", DEFAULT_STUCKTOSHIP_BASE_URL),
        os.getenv("AQE_STUCKTOSHIP_API_KEY") or None,
    )


def _normalize_base_url(base_url: str) -> str:
    candidate = base_url.strip().rstrip("/")
    parsed = urlsplit(candidate)
    if (
        parsed.scheme not in {"http", "https"}
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
        or parsed.path
    ):
        raise ValueError("Base URL must be an HTTP(S) origin without credentials, path, query, or fragment.")
    return candidate


def _urllib_transport(
    url: str,
    payload: dict[str, object],
    headers: dict[str, str],
    timeout_seconds: float,
) -> tuple[int, str]:
    request_headers = {"Content-Type": "application/json", **headers}
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:  # noqa: S310 - explicit operator target
            return response.status, response.read().decode("utf-8")
    except HTTPError as error:
        raise StuckToShipTargetError(f"Target returned HTTP {error.code}.") from error
    except URLError as error:
        raise StuckToShipTargetError("Target request failed: network unavailable.") from error


def _parse_target_response(status: int, raw: str) -> StuckToShipResponse:
    if status < 200 or status >= 300:
        raise StuckToShipTargetError(f"Target returned HTTP {status}.")
    try:
        body = json.loads(raw)
    except json.JSONDecodeError as error:
        raise StuckToShipTargetError("Target returned malformed JSON.") from error
    if not isinstance(body, dict) or body.get("code") != 0:
        raise StuckToShipTargetError("Target returned a non-success response code.")
    data = body.get("data")
    if not isinstance(data, dict):
        raise StuckToShipTargetError("Target response is missing data.")
    answer = _required_string(data, "answer", target=True)
    route = _required_string(data, "route", target=True)
    trace = data.get("trace")
    if not isinstance(trace, dict):
        raise StuckToShipTargetError("Target response is missing trace.")
    references = data.get("references")
    if not isinstance(references, list):
        raise StuckToShipTargetError("Target response is missing references.")
    reference_ids = tuple(_reference_identity(reference) for reference in references)
    return StuckToShipResponse(
        answer=answer,
        reference_ids=reference_ids,
        route=route,
        trace=trace,
    )


def _reference_identity(reference: object) -> str:
    if not isinstance(reference, dict):
        raise StuckToShipTargetError("Target reference is not an object.")
    for key in ("source_path", "source_file", "document_id", "id"):
        value = reference.get(key)
        if isinstance(value, str) and value.strip():
            return value
    raise StuckToShipTargetError("Target reference has no stable identity.")


def _required_string(source: dict[str, object], key: str, *, target: bool = False) -> str:
    value = source.get(key)
    if not isinstance(value, str) or not value.strip():
        prefix = "Target response" if target else "Dataset case"
        raise StuckToShipTargetError(f"{prefix} is missing {key}.") if target else ValueError(f"missing {key}")
    return value


def _required_bool(source: dict[str, object], key: str) -> bool:
    value = source.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"missing boolean {key}")
    return value


def _required_strings(source: dict[str, object], key: str) -> tuple[str, ...]:
    value = source.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"missing string list {key}")
    return tuple(value)
