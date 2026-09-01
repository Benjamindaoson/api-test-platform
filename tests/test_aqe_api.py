from fastapi.testclient import TestClient

from api.main import app


def test_fixture_endpoint_exposes_contract_without_protected_markers():
    with TestClient(app) as client:
        response = client.get("/api/aqe/fixture")

    assert response.status_code == 200
    body = response.json()
    assert body["dataset_version"] == "rag-release-gate-v1"
    assert "baseline" in body["profiles"]
    assert {case["id"] for case in body["cases"]} == {
        "remote-work-policy",
        "out-of-scope-refusal",
        "prompt-injection-refusal",
    }
    assert "AQE_INTERNAL_POLICY" not in response.text


def test_release_gate_endpoint_returns_baseline_pass_evidence():
    with TestClient(app) as client:
        response = client.post("/api/aqe/runs", json={"profile": "baseline"})

    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "pass"
    assert len(body["case_results"]) == 3
    assert body["case_results"][0]["response"]["profile"] == "baseline"


def test_release_gate_endpoint_returns_block_evidence_for_injected_leak():
    with TestClient(app) as client:
        response = client.post(
            "/api/aqe/runs",
            json={"profile": "prompt-injection-leak"},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["verdict"] == "block"
    assert any(
        finding["rule_id"] == "protected-marker"
        for result in body["case_results"]
        for finding in result["findings"]
    )
    assert "AQE_INTERNAL_POLICY" not in response.text


def test_release_gate_endpoint_rejects_unknown_profile():
    with TestClient(app) as client:
        response = client.post("/api/aqe/runs", json={"profile": "not-a-profile"})

    assert response.status_code == 422
    assert "Unknown AQE fixture profile" in response.json()["detail"]


def test_openapi_declares_structured_aqe_response_models():
    with TestClient(app) as client:
        schema = client.get("/openapi.json").json()

    run_schema = schema["paths"]["/api/aqe/runs"]["post"]["responses"]["200"]
    fixture_schema = schema["paths"]["/api/aqe/fixture"]["get"]["responses"]["200"]
    assert run_schema["content"]["application/json"]["schema"]["$ref"].endswith(
        "/AQEReleaseEvidenceResponse",
    )
    assert fixture_schema["content"]["application/json"]["schema"]["$ref"].endswith(
        "/AQEFixtureResponse",
    )


def test_benchmark_endpoint_returns_bounded_detection_report():
    with TestClient(app) as client:
        response = client.get("/api/aqe/benchmark")

    assert response.status_code == 200
    body = response.json()
    assert body["corpus"] == "built-in-fixture"
    assert body["detection_rate"] == 1.0
    assert body["detected_scenarios"] == 5
    assert len(body["scenarios"]) == 5
