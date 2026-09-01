# RAG Release Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic local RAG fixture and an unattended FastAPI release gate that returns evidence-backed `pass`, `block`, or `escalate` decisions.

**Architecture:** A new `aqe` package separates versioned dataset loading, deterministic fixture behavior, evaluators, and policy orchestration. `api/main.py` only validates HTTP input and serializes the evidence package, leaving existing API-test persistence untouched.

**Tech Stack:** Python 3.13, standard library dataclasses and JSON, FastAPI, Pydantic, pytest, FastAPI TestClient.

**Spec:** `openspec/changes/rag-release-gate/design.md`

## Global Constraints

- No new dependency, database migration, external API call, model call, or vector database is permitted.
- All release-blocking findings are deterministic and preserve the inspected response in evidence.
- `baseline`, `wrong-retrieval`, `ungrounded-answer`, `fabricated-citation`, `unsafe-refusal`, and `prompt-injection-leak` are the complete v0.1 fault-profile contract.
- New production behavior is written only after its corresponding pytest assertion has failed for the expected reason.

---

### Task 1: Domain data, dataset loader, and fixture target

**Files:**
- Create: `aqe/__init__.py`
- Create: `aqe/models.py`
- Create: `aqe/dataset.py`
- Create: `aqe/fixture.py`
- Create: `aqe/fixtures/rag_release_gate_v1.json`
- Create: `tests/test_aqe_fixture.py`

**Interfaces:**
- Produces `EvaluationCase`, `EvaluationDataset`, `FixtureResponse`, `FaultProfile`, `load_dataset()`, `supported_profiles()`, and `run_fixture(case, profile)`.
- Consumed by Task 2.

- [ ] **Step 1: Write the failing fixture tests**

```python
from aqe.dataset import load_dataset
from aqe.fixture import run_fixture

def test_baseline_returns_grounded_answer_with_required_citation():
    case = load_dataset().cases[0]
    response = run_fixture(case, "baseline")
    assert case.expected_answer_fragment in response.answer
    assert response.citations == case.expected_citations
    assert response.refused is False

def test_unknown_input_refuses_without_evidence():
    response = run_fixture_for_input("unlisted question", "baseline")
    assert response.refused is True
    assert response.citations == ()
    assert response.retrieved_document_ids == ()
```

- [ ] **Step 2: Run the tests to verify the expected missing-module failure**

Run: `uv run python -m pytest tests/test_aqe_fixture.py -v`

Expected: FAIL because the `aqe` package does not exist.

- [ ] **Step 3: Implement typed dataset loading and deterministic fixture responses**

```python
@dataclass(frozen=True)
class FixtureResponse:
    answer: str
    retrieved_document_ids: tuple[str, ...]
    citations: tuple[str, ...]
    refused: bool
    profile: str

def run_fixture(case: EvaluationCase, profile: str) -> FixtureResponse:
    validate_profile(profile)
    return response_for_case(case, profile)
```

Store the baseline response fields in the checked-in JSON dataset and make each profile alter only its declared observable failure condition.

- [ ] **Step 4: Run the fixture tests and profile matrix**

Run: `uv run python -m pytest tests/test_aqe_fixture.py -v`

Expected: PASS for baseline, unknown input, and every named profile.

- [ ] **Step 5: Commit the isolated target slice**

```bash
git add aqe tests/test_aqe_fixture.py
git commit -m "feat: add deterministic RAG fixture target"
```

### Task 2: Deterministic evaluators and release policy

**Files:**
- Create: `aqe/evaluators.py`
- Create: `aqe/runner.py`
- Create: `tests/test_aqe_release_gate.py`

**Interfaces:**
- Consumes `EvaluationCase`, `FixtureResponse`, and `run_fixture` from Task 1.
- Produces `RuleFinding`, `CaseResult`, `EvidencePackage`, `evaluate_case(case, response)`, and `run_release_gate(profile="baseline")`.
- Consumed by Task 3.

- [ ] **Step 1: Write failing release-policy tests**

```python
import pytest
from aqe.runner import run_release_gate

def test_baseline_profile_passes_every_case():
    evidence = run_release_gate("baseline")
    assert evidence.verdict == "pass"
    assert all(result.passed for result in evidence.case_results)

@pytest.mark.parametrize("profile", [
    "wrong-retrieval", "ungrounded-answer", "fabricated-citation",
    "unsafe-refusal", "prompt-injection-leak",
])
def test_injected_critical_fault_blocks_with_rule_evidence(profile):
    evidence = run_release_gate(profile)
    assert evidence.verdict == "block"
    assert any(result.findings for result in evidence.case_results if not result.passed)
```

- [ ] **Step 2: Run tests to verify the expected missing-runner failure**

Run: `uv run python -m pytest tests/test_aqe_release_gate.py -v`

Expected: FAIL because `aqe.runner` does not exist.

- [ ] **Step 3: Implement rule evaluation and policy aggregation**

```python
def evaluate_case(case: EvaluationCase, response: FixtureResponse) -> CaseResult:
    findings = tuple(
        finding for finding in (
            check_answer(case, response), check_citations(case, response),
            check_refusal(case, response), check_protected_markers(case, response),
        ) if finding is not None
    )
    return CaseResult(case_id=case.id, severity=case.severity,
                      passed=not findings, findings=findings, response=response)
```

The runner returns `block` for any failed critical case, `escalate` for a failed non-critical case or invalid/no executable dataset, and `pass` only for all-pass evidence.

- [ ] **Step 4: Run the release-policy tests**

Run: `uv run python -m pytest tests/test_aqe_release_gate.py -v`

Expected: PASS for the baseline and every injected fault profile.

- [ ] **Step 5: Commit the quality policy slice**

```bash
git add aqe tests/test_aqe_release_gate.py
git commit -m "feat: add RAG release gate evaluation"
```

### Task 3: FastAPI management routes

**Files:**
- Modify: `api/main.py`
- Create: `tests/test_aqe_api.py`

**Interfaces:**
- Consumes `fixture_metadata()` and `run_release_gate(profile)` from Tasks 1–2.
- Produces `GET /api/aqe/fixture` and `POST /api/aqe/runs`.

- [ ] **Step 1: Write failing HTTP contract tests**

```python
from fastapi.testclient import TestClient
from api.main import app

def test_fixture_endpoint_hides_protected_markers():
    response = TestClient(app).get("/api/aqe/fixture")
    assert response.status_code == 200
    assert "baseline" in response.json()["profiles"]
    assert "protected_markers" not in response.text

def test_release_gate_endpoint_blocks_injected_leak():
    response = TestClient(app).post("/api/aqe/runs", json={"profile": "prompt-injection-leak"})
    assert response.status_code == 200
    assert response.json()["verdict"] == "block"
```

- [ ] **Step 2: Run tests to verify the expected missing-route failure**

Run: `uv run python -m pytest tests/test_aqe_api.py -v`

Expected: FAIL with HTTP 404 because `/api/aqe/*` routes do not exist.

- [ ] **Step 3: Add Pydantic request validation and routes**

```python
class AQERunRequest(BaseModel):
    profile: str = "baseline"

@app.post("/api/aqe/runs")
async def run_aqe_release_gate(body: AQERunRequest):
    try:
        return run_release_gate(body.profile).to_dict()
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
```

`GET /api/aqe/fixture` returns only version, profile names, and case identifiers/severities; it never serializes protected marker values.

- [ ] **Step 4: Run the HTTP contract suite**

Run: `uv run python -m pytest tests/test_aqe_api.py -v`

Expected: PASS for metadata, baseline, block evidence, and unknown-profile validation.

- [ ] **Step 5: Commit the management API slice**

```bash
git add api/main.py tests/test_aqe_api.py
git commit -m "feat: expose RAG release gate API"
```

### Task 4: Documentation and executable verification

**Files:**
- Modify: `README.md`
- Modify: `openspec/changes/rag-release-gate/tasks.md`

**Interfaces:**
- Documents the two new HTTP routes and all supported profiles.

- [ ] **Step 1: Add an AQE quick-start section to the README**

```markdown
curl -X POST http://localhost:8100/api/aqe/runs \
  -H "Content-Type: application/json" \
  -d '{"profile":"baseline"}'
```

Document that a baseline returns `pass` and an injected profile returns `block`; explain that it is an internal deterministic target, not a claim about a real customer deployment.

- [ ] **Step 2: Run specification validation**

Run: `openspec validate rag-release-gate --strict`

Expected: exit code 0.

- [ ] **Step 3: Run Python verification**

Run: `uv run python -m pytest tests/test_aqe_fixture.py tests/test_aqe_release_gate.py tests/test_aqe_api.py -v` and `uv run python -m compileall -q aqe api`

Expected: all tests pass and compile command exits 0.

- [ ] **Step 4: Run a live HTTP smoke test**

Run: start `uv run python -m uvicorn api.main:app --host 127.0.0.1 --port 8100`, then send `Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8100/api/aqe/runs -ContentType application/json -Body '{"profile":"baseline"}'`.

Expected: response verdict is `pass` and contains every evaluated case.

- [ ] **Step 5: Commit the documentation and verified change artifacts**

```bash
git add README.md CONTEXT.md docs openspec
git commit -m "docs: specify RAG release gate"
```
