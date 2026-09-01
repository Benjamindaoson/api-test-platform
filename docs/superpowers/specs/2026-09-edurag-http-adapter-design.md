# EduRAG HTTP Adapter Design

**Goal:** Turn StuckToShip’s existing RAG question-answer endpoint into the first real AQE target, producing honest quality evidence without exposing a generic remote-execution API.

## Contract

AQE sends only `POST {base_url}/api/v1/rag/ask` with a query, `stream: false`, and isolated `session_id`. A valid target response is `code: 0` plus `data.answer`, `data.references`, `data.route`, and `data.trace`. A target execution issue produces `escalate`; a valid response that violates expected quality produces `block`.

## Corpus

`stucktoship-rag-v1` contains four stable questions sourced from StuckToShip’s own Agent Course evaluation corpus: one each for `course`, `code`, `faq`, and `clarify`. The first three require citations and small case-specific answer assertions; `clarify` requires its trace decision to be `clarify` and does not require citations. This catches a cited but wrong code-symbol answer.

## Safety boundary

The adapter is an in-process CLI capability. It does not add a `base_url`-accepting FastAPI route, does not write target data, and only reads the optional API key from `AQE_STUCKTOSHIP_API_KEY`. That value is never returned or written into evidence.

## Proof

Unit tests exercise a transport seam and malformed/failed responses. The final smoke run starts the local EduRAG project at `http://127.0.0.1:8010` and invokes AQE against it.
