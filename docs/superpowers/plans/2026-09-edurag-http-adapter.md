# EduRAG HTTP Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only, evidence-backed AQE runner for the local StuckToShip (EduRAG) HTTP API.

**Architecture:** Keep the original deterministic Fixture Gate unchanged. A new adapter performs one non-streaming HTTP call through an injected transport, while a dedicated gate evaluates StuckToShip-specific route, citation, and clarification requirements. The CLI is local-only configuration, not a new platform API.

**Tech Stack:** Python 3.12, standard-library `urllib`, Pydantic/FastAPI already present, pytest, OpenSpec.

**Spec:** `openspec/changes/edurag-http-adapter/design.md`

## Global Constraints

- Do not add third-party dependencies.
- Do not add a FastAPI endpoint accepting a target base URL.
- Do not write to EduRAG’s API, knowledge base, indexes, or database.
- Do not emit `AQE_STUCKTOSHIP_API_KEY` in JSON evidence, exceptions, or logs.
- Use `uv run python -m pytest`, not the blocked `uv run pytest` launcher.

---

### Task 1: Define the target contract and corpus

**Files:**
- Create: `aqe/stucktoship.py`
- Create: `aqe/fixtures/stucktoship_rag_v1.json`
- Create: `tests/test_stucktoship_adapter.py`

**Interfaces:**
- Produces: `StuckToShipCase`, `StuckToShipResponse`, `StuckToShipTargetError`, and `StuckToShipClient.ask(case)`.
- Consumes: a callable with signature `(url: str, payload: dict[str, object], headers: dict[str, str], timeout_seconds: float) -> tuple[int, str]`.

- [ ] **Step 1: Write the failing contract tests**

```python
def test_client_normalizes_a_successful_target_response():
    client = StuckToShipClient(transport=lambda *_: (200, SUCCESS_JSON))
    response = client.ask(CASE)
    assert response.route == "course"
    assert response.reference_ids == ("knowledge/courses/rag-basics.md",)

def test_client_rejects_missing_trace_as_contract_failure():
    client = StuckToShipClient(transport=lambda *_: (200, '{"code": 0, "data": {"answer": "x", "references": [], "route": "course"}}'))
    with pytest.raises(StuckToShipTargetError, match="trace"):
        client.ask(CASE)
```

- [ ] **Step 2: Run the focused tests and observe failure**

Run: `uv run python -m pytest tests/test_stucktoship_adapter.py -q`

Expected: FAIL because `aqe.stucktoship` does not exist.

- [ ] **Step 3: Implement the smallest typed client and corpus loader**

```python
class StuckToShipClient:
    def ask(self, case: StuckToShipCase) -> StuckToShipResponse:
        status, raw = self._transport(self._ask_url(), self._payload(case), self._headers(), self.timeout_seconds)
        return _parse_target_response(status, raw)
```

- [ ] **Step 4: Re-run focused tests**

Run: `uv run python -m pytest tests/test_stucktoship_adapter.py -q`

Expected: PASS.

### Task 2: Implement target-specific evidence rules

**Files:**
- Create: `aqe/stucktoship_gate.py`
- Create: `tests/test_stucktoship_gate.py`

**Interfaces:**
- Consumes: `StuckToShipClient.ask(case)` and the versioned corpus.
- Produces: `StuckToShipEvidence` with `verdict` in `pass | block | escalate` and per-case finding IDs.

- [ ] **Step 1: Write failing gate tests**

```python
def test_missing_citation_blocks_an_answerable_case():
    evidence = run_stucktoship_gate(client=FakeClient(route="course", references=()))
    assert evidence.verdict == "block"
    assert "citation-presence" in evidence.rule_ids

def test_unreachable_target_escalates_not_passes():
    evidence = run_stucktoship_gate(client=FailingClient())
    assert evidence.verdict == "escalate"
```

- [ ] **Step 2: Run the focused tests and observe failure**

Run: `uv run python -m pytest tests/test_stucktoship_gate.py -q`

Expected: FAIL because the gate does not exist.

- [ ] **Step 3: Implement route/citation/clarification rules**

```python
if target_error:
    return _escalate(case.id, safe_reason)
if response.route != case.expected_route:
    findings.append("route")
if case.citation_required and not response.reference_ids:
    findings.append("citation-presence")
```

- [ ] **Step 4: Re-run focused tests**

Run: `uv run python -m pytest tests/test_stucktoship_gate.py -q`

Expected: PASS.

### Task 3: Add unattended local entry point and documentation

**Files:**
- Modify: `aqe/stucktoship_gate.py`
- Modify: `README.md`
- Modify: `openspec/changes/edurag-http-adapter/tasks.md`

**Interfaces:**
- Produces: `python -m aqe.stucktoship_gate [--base-url URL]` JSON output and status code 0 for pass, 1 for block, 2 for escalate.

- [ ] **Step 1: Write a failing CLI test**

```python
def test_cli_defaults_to_local_edurag_url(monkeypatch, capsys):
    monkeypatch.delenv("AQE_STUCKTOSHIP_BASE_URL", raising=False)
    exit_code = main([], client_factory=recording_factory)
    assert recording_factory.base_url == "http://127.0.0.1:8010"
    assert exit_code == 0
```

- [ ] **Step 2: Run the CLI test and observe failure**

Run: `uv run python -m pytest tests/test_stucktoship_gate.py -q`

Expected: FAIL because `main` and the default selection do not exist.

- [ ] **Step 3: Implement CLI and operator documentation**

```python
def main(argv: list[str] | None = None) -> int:
    args = parser.parse_args(argv)
    evidence = run_stucktoship_gate(base_url=args.base_url)
    print(json.dumps(evidence.to_dict(), ensure_ascii=False))
    return {"pass": 0, "block": 1, "escalate": 2}[evidence.verdict]
```

- [ ] **Step 4: Re-run focused tests**

Run: `uv run python -m pytest tests/test_stucktoship_adapter.py tests/test_stucktoship_gate.py -q`

Expected: PASS.

### Task 4: Verify the real target and complete the change

**Files:**
- Modify: `openspec/changes/edurag-http-adapter/tasks.md`

- [ ] **Step 1: Run static and repository verification**

Run: `uv run python -m pytest tests -q`; `uv run python -m compileall -q aqe api`; `openspec validate edurag-http-adapter --strict`

Expected: all commands pass.

- [ ] **Step 2: Run the real local HTTP gate**

Run: `uv run python -m aqe.stucktoship_gate --base-url http://127.0.0.1:8010`

Expected: JSON evidence with `target=stucktoship-rag-v1`; a non-pass is reported truthfully as a product/infra finding, not hidden.

- [ ] **Step 3: Mark OpenSpec tasks complete after successful evidence**

```markdown
- [x] 3.2 Start the local EduRAG target and execute the real HTTP smoke run without mutating target knowledge or state.
```

- [ ] **Step 4: Commit the verified implementation**

```bash
git add aqe tests README.md openspec/changes/edurag-http-adapter docs/superpowers
git commit -m "feat: add StuckToShip RAG quality adapter"
```
