from __future__ import annotations

import asyncio
import json
from pathlib import Path

import api.main as management_api


ROOT = Path(__file__).resolve().parents[1]


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_ui_image_has_a_locked_pnpm_production_build_contract():
    dockerfile = _read("ui/Dockerfile")

    assert "FROM node:22" in dockerfile
    assert "pnpm install --frozen-lockfile" in dockerfile
    assert "pnpm build" in dockerfile
    assert 'CMD ["pnpm", "start"]' in dockerfile
    assert "ARG NEXT_PUBLIC_MANAGEMENT_API_URL" in dockerfile


def test_ui_build_context_excludes_host_generated_artifacts():
    dockerignore = _read("ui/.dockerignore")

    assert "node_modules" in dockerignore
    assert ".next" in dockerignore


def test_python_images_match_the_python_313_lockfile_contract():
    for relative_path in ("Dockerfile.api", "Dockerfile.langgraph"):
        dockerfile = _read(relative_path)
        assert "FROM python:3.13-slim" in dockerfile
        assert "uv sync --locked" in dockerfile

    dockerignore = _read(".dockerignore")
    assert ".env" in dockerignore


def test_management_api_runtime_declares_its_server_and_test_executor():
    project = _read("pyproject.toml")

    assert '"uvicorn[standard]' in project
    assert '"pytest>=' in project

    api = _read("api/main.py")
    assert "INSERT INTO reports" in api


def test_compose_has_a_model_free_platform_profile_with_readiness_checks():
    compose = _read("docker-compose.yml")

    assert "platform" in compose
    assert "agent" in compose
    assert "condition: service_healthy" in compose
    assert "start_period:" in compose
    assert "ui:" in compose
    assert "api:" in compose
    assert "POSTGRES_EXTERNAL_PORT" in compose
    assert "REDIS_EXTERNAL_PORT" in compose
    assert "API_TEST_DIR: /app/workspace/test_suites" in compose
    assert "POSTGRES_DB: ${POSTGRES_DB:-api_test_platform}" in compose
    assert "POSTGRES_USER: ${POSTGRES_USER:-postgres}" in compose
    assert "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}" in compose
    assert "NEXT_PUBLIC_MANAGEMENT_API_URL: http://localhost:${API_EXTERNAL_PORT:-8100}" in compose


def test_delivery_workflow_runs_frontend_and_compose_smoke_gates():
    workflow = _read(".github/workflows/platform-delivery.yml")

    assert "pnpm install --frozen-lockfile" in workflow
    assert "pnpm build" in workflow
    assert "docker compose --profile platform up --build --wait" in workflow
    assert "python scripts/e2e_smoke.py" in workflow
    assert "playwright install --with-deps chromium" in workflow
    assert "management-flow.spec.ts" in workflow


def test_repository_contains_disposable_e2e_inputs_and_runner():
    assert (ROOT / "tests/fixtures/e2e_openapi.yaml").is_file()
    assert (ROOT / "tests/fixtures/e2e_generated_test.py").is_file()

    runner = _read("scripts/e2e_smoke.py")
    assert "def run_smoke" in runner
    assert "SmokeFailure" in runner


def test_endpoint_sync_serializes_jsonb_fields_for_asyncpg(monkeypatch):
    executed: list[tuple[object, ...]] = []

    class Connection:
        async def fetchrow(self, *_args):
            return {"openapi_spec": "fixture.yaml"}

        async def execute(self, *args):
            executed.append(args)

    class Acquire:
        async def __aenter__(self):
            return Connection()

        async def __aexit__(self, *_args):
            return False

    class Pool:
        def acquire(self):
            return Acquire()

    async def parsed_openapi(*_args):
        return json.dumps(
            {
                "title": "fixture",
                "version": "1.0.0",
                "endpoints": [
                    {
                        "path": "/ping",
                        "method": "GET",
                        "summary": "Ping",
                        "tags": ["smoke"],
                        "parameters": [],
                        "request_body": {"required": False},
                        "responses": {"200": {"description": "ok"}},
                    }
                ],
            }
        )

    monkeypatch.setattr(management_api, "get_db_pool", lambda: Pool())
    monkeypatch.setattr(management_api, "run_in_threadpool", parsed_openapi)

    result = asyncio.run(
        management_api.sync_endpoints(management_api.EndpointSyncRequest(project_id="project-id"))
    )

    assert result["synced"] == 1
    assert executed[0][5] == ["smoke"]
    assert json.loads(executed[0][6]) == []
    assert json.loads(executed[0][7]) == {"required": False}
    assert json.loads(executed[0][8]) == {"200": {"description": "ok"}}


def test_health_performs_a_database_round_trip_before_reporting_connected(monkeypatch):
    queries: list[str] = []

    class Connection:
        async def execute(self, query: str):
            queries.append(query)

    class Acquire:
        async def __aenter__(self):
            return Connection()

        async def __aexit__(self, *_args):
            return False

    class Pool:
        def acquire(self):
            return Acquire()

    monkeypatch.setattr(management_api, "get_db_pool", lambda: Pool())

    health = asyncio.run(management_api.health())

    assert health["status"] == "ok"
    assert health["database"] == "connected"
    assert queries == ["SELECT 1"]
