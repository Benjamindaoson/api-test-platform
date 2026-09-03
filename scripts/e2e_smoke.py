from __future__ import annotations

import argparse
import json
import time
from collections.abc import Callable
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_OPENAPI_PATH = "/app/tests/fixtures/e2e_openapi.yaml"
DEFAULT_TEST_PATH = "/app/tests/fixtures/e2e_generated_test.py"


class SmokeFailure(RuntimeError):
    """Raised when the public management-platform smoke contract is not met."""


RequestJson = Callable[[str, str, dict[str, object] | None], object]


def _http_request_json(base_url: str) -> RequestJson:
    normalized_base_url = base_url.rstrip("/")

    def request_json(method: str, path: str, payload: dict[str, object] | None) -> object:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(
            f"{normalized_base_url}{path}",
            data=body,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urlopen(request, timeout=10) as response:  # noqa: S310
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:500]
            raise SmokeFailure(f"{method} {path} returned HTTP {error.code}: {detail}") from error
        except URLError as error:
            raise SmokeFailure(f"{method} {path} could not reach the API: {error.reason}") from error

    return request_json


def _mapping(value: object, *, step: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SmokeFailure(f"{step} returned {type(value).__name__}, expected a JSON object.")
    return value


def _wait_for_healthy_api(request_json: RequestJson, *, timeout_seconds: float) -> None:
    deadline = time.monotonic() + max(timeout_seconds, 0)
    last_response: object = None
    last_error: Exception | None = None
    while True:
        try:
            last_response = request_json("GET", "/health", None)
            health = _mapping(last_response, step="GET /health")
            if health.get("status") == "ok" and health.get("database") == "connected":
                return
        except SmokeFailure as error:
            last_error = error
        if time.monotonic() >= deadline:
            detail = str(last_error) if last_error else json.dumps(last_response, ensure_ascii=False)
            raise SmokeFailure(f"API did not become database healthy before timeout: {detail}")
        time.sleep(min(1.0, max(0.0, deadline - time.monotonic())))


def run_smoke(
    base_url: str,
    *,
    timeout_seconds: float = 60,
    request_json: RequestJson | None = None,
    openapi_path: str = DEFAULT_OPENAPI_PATH,
    test_path: str = DEFAULT_TEST_PATH,
) -> dict[str, object]:
    """Exercise the public persistence-backed management workflow in order."""
    requester = request_json or _http_request_json(base_url)
    _wait_for_healthy_api(requester, timeout_seconds=timeout_seconds)
    project = _mapping(
        requester("POST", "/api/projects", {"name": "delivery-smoke", "openapi_spec": openapi_path, "base_url": "http://example.invalid"}),
        step="POST /api/projects",
    )
    project_id = project.get("id")
    if not isinstance(project_id, str) or not project_id:
        raise SmokeFailure("POST /api/projects did not return a project id.")
    synced = _mapping(requester("POST", "/api/endpoints/sync", {"project_id": project_id}), step="POST /api/endpoints/sync")
    synced_endpoints = synced.get("synced")
    if not isinstance(synced_endpoints, int) or synced_endpoints < 1:
        raise SmokeFailure("POST /api/endpoints/sync did not persist an endpoint.")
    endpoints = requester("GET", f"/api/endpoints?project_id={project_id}", None)
    if not isinstance(endpoints, list) or not any(isinstance(endpoint, dict) and endpoint.get("path") == "/ping" and endpoint.get("method") == "GET" for endpoint in endpoints):
        raise SmokeFailure("GET /api/endpoints did not return the synchronized /ping endpoint.")
    execution = _mapping(requester("POST", "/api/test", {"project_id": project_id, "test_path": test_path}), step="POST /api/test")
    run_id = execution.get("run_id")
    if execution.get("status") != "passed" or not isinstance(run_id, str) or not run_id:
        raise SmokeFailure(f"POST /api/test did not pass: {json.dumps(execution, ensure_ascii=False)}")
    run_detail = _mapping(requester("GET", f"/api/runs/{run_id}", None), step="GET /api/runs/{run_id}")
    run = _mapping(run_detail.get("run"), step="GET /api/runs/{run_id}.run")
    results = run_detail.get("results")
    if run.get("status") != "passed" or not isinstance(results, list) or not results:
        raise SmokeFailure("GET /api/runs/{run_id} did not return a persisted passing result.")
    reports = requester("GET", f"/api/reports?project_id={project_id}", None)
    if not isinstance(reports, list) or not any(
        isinstance(report, dict) and report.get("project_id") == project_id and report.get("report_type") == "test_run"
        for report in reports
    ):
        raise SmokeFailure("GET /api/reports did not return a persisted test report.")
    return {"project_id": project_id, "run_id": run_id, "synced_endpoints": synced_endpoints, "run_status": run["status"]}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run the disposable API platform delivery smoke flow.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8100")
    parser.add_argument("--timeout-seconds", type=float, default=60)
    args = parser.parse_args(argv)
    try:
        result = run_smoke(args.base_url, timeout_seconds=args.timeout_seconds)
    except SmokeFailure as error:
        print(json.dumps({"status": "failed", "error": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps({"status": "passed", **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
