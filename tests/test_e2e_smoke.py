from __future__ import annotations

import json

import pytest

from scripts.e2e_smoke import SmokeFailure, run_smoke


def test_run_smoke_exercises_the_persistence_backed_management_flow():
    requests: list[tuple[str, str, dict[str, object] | None]] = []
    project_id = "00000000-0000-0000-0000-000000000001"
    run_id = "00000000-0000-0000-0000-000000000002"

    def request_json(method: str, path: str, payload: dict[str, object] | None):
        requests.append((method, path, payload))
        responses = {
            ("GET", "/health"): {"status": "ok", "database": "connected"},
            ("POST", "/api/projects"): {"id": project_id, "name": "delivery-smoke"},
            ("POST", "/api/endpoints/sync"): {"project_id": project_id, "synced": 1},
            ("GET", f"/api/endpoints?project_id={project_id}"): [
                {"path": "/ping", "method": "GET"},
            ],
            ("POST", "/api/test"): {"run_id": run_id, "status": "passed"},
            ("GET", f"/api/runs/{run_id}"): {
                "run": {"id": run_id, "status": "passed"},
                "results": [{"status": "passed"}],
            },
            ("GET", f"/api/reports?project_id={project_id}"): [
                {"project_id": project_id, "report_type": "test_run"},
            ],
        }
        return responses[(method, path)]

    result = run_smoke(
        "http://platform.test",
        timeout_seconds=0,
        request_json=request_json,
    )

    assert result == {
        "project_id": project_id,
        "run_id": run_id,
        "synced_endpoints": 1,
        "run_status": "passed",
    }
    assert [(method, path) for method, path, _ in requests] == [
        ("GET", "/health"),
        ("POST", "/api/projects"),
        ("POST", "/api/endpoints/sync"),
        ("GET", f"/api/endpoints?project_id={project_id}"),
        ("POST", "/api/test"),
        ("GET", f"/api/runs/{run_id}"),
        ("GET", f"/api/reports?project_id={project_id}"),
    ]
    assert requests[1][2] == {
        "name": "delivery-smoke",
        "openapi_spec": "/app/tests/fixtures/e2e_openapi.yaml",
        "base_url": "http://example.invalid",
    }
    assert requests[4][2] == {
        "project_id": project_id,
        "test_path": "/app/tests/fixtures/e2e_generated_test.py",
    }


def test_run_smoke_includes_last_health_response_when_api_never_becomes_ready():
    def request_json(method: str, path: str, payload: dict[str, object] | None):
        assert (method, path, payload) == ("GET", "/health", None)
        return {"status": "degraded", "database": "disconnected"}

    with pytest.raises(SmokeFailure, match="degraded"):
        run_smoke(
            "http://platform.test",
            timeout_seconds=0,
            request_json=request_json,
        )
