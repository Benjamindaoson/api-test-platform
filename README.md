# API Test Platform

> **Turn a code change or OpenAPI document into an explainable, prioritized API test plan — then execute it and keep the evidence.**

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/Python-3.13%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-000000?logo=nextdotjs)](ui/package.json)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-1C3C3C)](https://langchain-ai.github.io/langgraph/)

**API Test Platform** is an agent-assisted API quality workspace for engineering teams. It combines repository-aware impact analysis, OpenAPI-driven test generation, test execution, contract validation, and reporting behind a conversational interface and management API.

> 中文简介：这是一个面向企业研发团队的智能 API 测试平台。它将代码变更影响分析、OpenAPI 测试生成、执行、契约校验和报告汇总为一个可追溯的工作流。

## Why this exists

Most API testing breaks down at the hand-off between a code change and the regression suite. Teams either run too little and miss regressions, or run everything and wait too long. This project focuses on the missing decision layer:

1. **What changed?** Inspect the affected code and routes.
2. **What should be tested?** Recommend a focused regression scope and generate cases from the API contract.
3. **What happened?** Execute tests, validate contracts, and produce an actionable report.

The result is intended to make API quality work more targeted, legible, and repeatable — not to replace engineering judgment.

## Capabilities

| Workflow | What the platform does |
| --- | --- |
| Change-aware regression | Uses CodeGraph tooling to explore code and identify API routes that deserve regression attention. |
| OpenAPI test generation | Parses OpenAPI/Swagger specifications and produces positive, negative, and boundary-oriented test cases and pytest scripts. |
| Test execution | Runs smoke, regression, and generated API tests with pytest-based tooling. |
| Contract validation | Uses Schemathesis-oriented tooling to validate an API against its OpenAPI contract. |
| Multi-agent orchestration | A supervisor coordinates code analysis, testing, test generation, and report-writing agents. |
| Evidence and operations | A FastAPI management API and web UI expose projects, endpoints, runs, and reports. |

## AQE preview: deterministic RAG Release Gate

The repository now includes the first executable slice of **Agent Quality Engineer (AQE)**: a deterministic local RAG target and an unattended quality gate. It is deliberately a test target, not a claim that this repository has evaluated a real production RAG deployment.

The fixture exercises a release gate across a versioned dataset with three critical scenarios: a grounded answer with a valid citation, an out-of-scope refusal, and resistance to prompt injection. Named profiles inject one reproducible failure:

| Profile | Injected failure | Expected verdict |
| --- | --- | --- |
| `baseline` | No injected failure | `pass` |
| `wrong-retrieval` | Citation is not among retrieved documents | `block` |
| `ungrounded-answer` | Required answer evidence is missing | `block` |
| `fabricated-citation` | Response cites a fabricated document | `block` |
| `unsafe-refusal` | A request requiring refusal gets an answer | `block` |
| `prompt-injection-leak` | A protected marker appears in the response | `block` |

Start the management API and execute a gate locally:

```bash
python -m uvicorn api.main:app --host 127.0.0.1 --port 8100
```

```bash
curl -X POST http://127.0.0.1:8100/api/aqe/runs \
  -H "Content-Type: application/json" \
  -d '{"profile":"baseline"}'
```

Use `GET /api/aqe/fixture` to inspect the public dataset contract. The response includes the dataset version, profiles, case identifiers, and severities; it intentionally excludes protected markers. Every run returns an evidence package containing response snapshots, failed rule identifiers, and a `pass`, `block`, or `escalate` verdict.

## Architecture

```text
                        ┌──────────────────────────────┐
                        │  Next.js 15 + React 19 UI    │
                        │  chat workspace + admin UI   │
                        └──────────────┬───────────────┘
                                       │
                 ┌─────────────────────┴─────────────────────┐
                 │                                           │
      ┌──────────▼──────────┐                    ┌───────────▼───────────┐
      │ LangGraph / DeepAgents│                    │ FastAPI management API │
      │ supervisor            │                    │ projects, runs, reports│
      └──────────┬───────────┘                    └───────────┬───────────┘
                 │                                            │
   ┌─────────────┼──────────────┬──────────────┐      ┌───────▼───────┐
   │             │              │              │      │ PostgreSQL    │
   ▼             ▼              ▼              ▼      │ Redis         │
Code analyzer  API tester  Test generator  Report writer│              │
   │             │              │              │      └───────────────┘
   └──── CodeGraph / OpenAPI / pytest / Schemathesis ──┘
```

## Quick start

### Prerequisites

- Python **3.13+**
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Node.js **22 LTS** and pnpm **10.5.1+**
- Docker Desktop (for PostgreSQL and Redis)
- An OpenAI-compatible API key
- [CodeGraph CLI](https://www.npmjs.com/package/codegraph) for code-impact analysis

### 1. Clone and configure

```bash
git clone https://github.com/Benjamindaoson/api-test-platform.git
cd api-test-platform

# Never commit this file.
cp .env.example .env
```

Set `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `MODEL_NAME`, `BACKEND_ROOT_DIR`, and `CODEGRAPH_DEFAULT_PROJECT` in `.env`. Use absolute paths for the two project-root variables.

### 2. Install dependencies

```bash
# Backend: uv creates an isolated .venv in this repository.
uv sync

# Code-impact analysis dependency
npm install --global codegraph

# Frontend
cd ui
pnpm install
cp .env.example .env
cd ..
```

### 3. Start local dependencies and services

```bash
# PostgreSQL and Redis only
docker compose up -d postgres redis

# Terminal 1: LangGraph agent server
uv run langgraph dev --host 0.0.0.0 --port 8200 --n-jobs-per-worker 10

# Terminal 2: Management API
uv run python -m uvicorn api.main:app --host 0.0.0.0 --port 8100 --reload

# Terminal 3: Web UI
cd ui && pnpm dev
```

Open:

- UI: <http://localhost:3000>
- Management API docs: <http://localhost:8100/docs>
- LangGraph development API: <http://localhost:8200>

### 4. Try a workflow

In the chat UI, ask one of the following:

```text
Analyze recent code changes and recommend the API regression scope.
Generate API test cases from swagger.json and execute them.
Validate this service against its OpenAPI specification and write a report.
```

## Configuration

| Variable | Purpose |
| --- | --- |
| `OPENAI_API_KEY` | API key for the configured model provider. Keep it out of version control. |
| `OPENAI_BASE_URL` | Base URL of an OpenAI-compatible model API. |
| `MODEL_NAME` | Model used by the agent supervisor and subagents. |
| `BACKEND_ROOT_DIR` | Filesystem root available to agent tools. Prefer a least-privilege project directory. |
| `BACKEND_VIRTUAL_MODE` | Set to `true` for stricter path isolation when analysing untrusted repositories. |
| `CODEGRAPH_DEFAULT_PROJECT` | Absolute path to the repository analysed by CodeGraph. |
| `POSTGRES_*` / `REDIS_*` | Local persistence and cache configuration. |
| `NEXT_PUBLIC_API_URL` | LangGraph server URL used by the UI. |
| `NEXT_PUBLIC_MANAGEMENT_API_URL` | Management API URL used by the UI. |

See [`.env.example`](.env.example) and [`ui/.env.example`](ui/.env.example) for the complete set of variables.

## Development

```bash
# Python tests (when test files are present)
uv run python -m pytest

# Frontend production build
cd ui && pnpm build

# Frontend formatting check
cd ui && pnpm format:check
```

The repository is currently an early open-source release. The full `docker compose up` experience is not yet supported because the UI image definition has not been added; use the local development flow above, or start only `postgres` and `redis` through Compose.

## Project layout

```text
.
├── agent.py              # LangGraph supervisor and agent assembly
├── agents/               # Code analysis, test, generation, and reporting agents
├── tools/                # CodeGraph, OpenAPI, test, and project tools
├── api/                  # FastAPI management API
├── services/             # Persistence services
├── migrations/           # PostgreSQL schema
├── ui/                   # Next.js chat and administration interface
├── docs/                 # Architecture and deployment notes
└── workspace/            # Local generated artifacts (not committed)
```

## Security model

This platform can execute test commands and inspect source code. Treat every configured project and model provider as part of your trust boundary.

- Use a dedicated, least-privilege workspace for `BACKEND_ROOT_DIR`.
- Keep `BACKEND_VIRTUAL_MODE=true` when analysing repositories you do not fully trust.
- Do not commit `.env`, generated reports, or API keys.
- Run the platform in an isolated environment before exposing it to untrusted specifications, repositories, or network targets.
- Please report vulnerabilities privately; see [SECURITY.md](SECURITY.md).

## Roadmap

- [ ] Production-ready UI Docker image and fully verified Compose deployment
- [ ] Repeatable end-to-end test fixtures and CI workflow
- [ ] Test-suite review and approval flows
- [ ] Pluggable test-result sinks and notifications
- [ ] More example projects and OpenAPI fixtures

## Contributing

Contributions, bug reports, and documentation improvements are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md), read the [Code of Conduct](CODE_OF_CONDUCT.md), and search existing issues before opening a new one.

## License and acknowledgements

This project is licensed under the [Apache License 2.0](LICENSE). The UI includes work derived from LangChain's [Agent Chat UI](https://github.com/langchain-ai/agent-chat-ui), which is available under the MIT License; see [NOTICE](NOTICE) and [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md) for attribution and terms.

---

**Build less test debt. Ship more confidence.**
