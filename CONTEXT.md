# Ubiquitous Language

## Agent Quality Engineer

The subsystem that produces a repeatable quality verdict for an AI application release. It is not a conversational agent and it does not modify application code.

## Evaluation Dataset

A versioned collection of evaluation cases. A case declares its input, expected answer evidence, expected citations, severity, and whether the application must refuse the request.

## Fixture RAG Service

A deterministic local RAG target used to prove evaluation behavior. A fault profile deliberately changes one part of its observable behavior without changing the evaluation dataset.

## Fault Profile

A named, deterministic injected failure mode such as `wrong-retrieval`, `ungrounded-answer`, `fabricated-citation`, `unsafe-refusal`, or `prompt-injection-leak`.

## Evaluator

A deterministic rule that evaluates one response against one evaluation case. The first release uses no LLM judge for release-blocking conclusions.

## Case Result

The per-case output containing the response snapshot, evaluator findings, severity, and pass or fail status.

## Release Verdict

The release-level decision: `pass`, `block`, or `escalate`. A critical failed case blocks a release; a run with no executable cases escalates instead of passing.

## Evidence Package

The immutable structured output of a release run: dataset version, fixture profile, per-case response snapshots, evaluator findings, aggregate verdict, and the reasons for that verdict.
