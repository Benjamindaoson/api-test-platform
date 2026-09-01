from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping


_DATASET_PATH = Path(__file__).with_name("fixtures") / "agent_tool_simulator_v1.json"


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    required_arguments: tuple[str, ...]
    allowed_roles: tuple[str, ...] = ("*",)
    behavior: str = "success"


@dataclass(frozen=True)
class ToolCall:
    tool_name: str
    arguments: Mapping[str, object]


@dataclass(frozen=True)
class ToolCallResult:
    call_index: int
    tool_name: str
    status: str
    rule_id: str | None = None


@dataclass(frozen=True)
class ToolGateEvidence:
    verdict: str
    reasons: tuple[str, ...]
    results: tuple[ToolCallResult, ...]

    @property
    def rule_ids(self) -> tuple[str, ...]:
        return tuple(result.rule_id for result in self.results if result.rule_id is not None)


@dataclass(frozen=True)
class ToolBenchmarkScenario:
    scenario_id: str
    expected_rule_id: str
    observed_rule_ids: tuple[str, ...]
    detected: bool


@dataclass(frozen=True)
class ToolBenchmarkReport:
    version: str
    total_scenarios: int
    detected_scenarios: int
    detection_rate: float
    scenarios: tuple[ToolBenchmarkScenario, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def run_tool_gate(
    tools: tuple[ToolDefinition, ...],
    *,
    role: str,
    calls: tuple[ToolCall, ...],
) -> ToolGateEvidence:
    definitions = {tool.name: tool for tool in tools}
    seen: set[tuple[str, str]] = set()
    results: list[ToolCallResult] = []
    for index, call in enumerate(calls):
        signature = (call.tool_name, json.dumps(dict(call.arguments), sort_keys=True, ensure_ascii=False))
        if signature in seen:
            results.append(ToolCallResult(index, call.tool_name, "blocked", "tool-duplicate"))
            continue
        seen.add(signature)
        definition = definitions.get(call.tool_name)
        if definition is None:
            results.append(ToolCallResult(index, call.tool_name, "blocked", "tool-unknown"))
        elif any(argument not in call.arguments for argument in definition.required_arguments):
            results.append(ToolCallResult(index, call.tool_name, "blocked", "tool-arguments"))
        elif "*" not in definition.allowed_roles and role not in definition.allowed_roles:
            results.append(ToolCallResult(index, call.tool_name, "blocked", "tool-permission"))
        elif definition.behavior == "timeout":
            results.append(ToolCallResult(index, call.tool_name, "blocked", "tool-timeout"))
        else:
            results.append(ToolCallResult(index, call.tool_name, "success"))
    rule_ids = tuple(result.rule_id for result in results if result.rule_id)
    if rule_ids:
        return ToolGateEvidence(
            verdict="block",
            reasons=tuple(f"Tool call violated {rule_id}." for rule_id in rule_ids),
            results=tuple(results),
        )
    return ToolGateEvidence(
        verdict="pass",
        reasons=("All simulated tool calls satisfied their declared contracts.",),
        results=tuple(results),
    )


def run_tool_simulator_benchmark() -> ToolBenchmarkReport:
    payload = json.loads(_DATASET_PATH.read_text(encoding="utf-8"))
    version = _required_string(payload, "version")
    tools = tuple(_load_tool(item) for item in _required_list(payload, "tools"))
    scenarios: list[ToolBenchmarkScenario] = []
    for raw_scenario in _required_list(payload, "scenarios"):
        scenario_id = _required_string(raw_scenario, "id")
        expected_rule_id = _required_string(raw_scenario, "expected_rule_id")
        calls = tuple(_load_call(item) for item in _required_list(raw_scenario, "calls"))
        evidence = run_tool_gate(tools, role=_required_string(raw_scenario, "role"), calls=calls)
        scenarios.append(
            ToolBenchmarkScenario(
                scenario_id=scenario_id,
                expected_rule_id=expected_rule_id,
                observed_rule_ids=evidence.rule_ids,
                detected=evidence.verdict == "block" and expected_rule_id in evidence.rule_ids,
            )
        )
    detected = sum(scenario.detected for scenario in scenarios)
    return ToolBenchmarkReport(
        version=version,
        total_scenarios=len(scenarios),
        detected_scenarios=detected,
        detection_rate=detected / len(scenarios) if scenarios else 0.0,
        scenarios=tuple(scenarios),
    )


def _load_tool(raw: object) -> ToolDefinition:
    if not isinstance(raw, dict):
        raise ValueError("Tool definition must be an object.")
    return ToolDefinition(
        name=_required_string(raw, "name"),
        required_arguments=tuple(_required_string_list(raw, "required_arguments")),
        allowed_roles=tuple(_required_string_list(raw, "allowed_roles")),
        behavior=str(raw.get("behavior", "success")),
    )


def _load_call(raw: object) -> ToolCall:
    if not isinstance(raw, dict) or not isinstance(raw.get("arguments"), dict):
        raise ValueError("Tool call must contain an arguments object.")
    return ToolCall(tool_name=_required_string(raw, "tool_name"), arguments=raw["arguments"])


def _required_string(payload: dict, key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"Expected non-empty string '{key}'.")
    return value


def _required_list(payload: dict, key: str) -> list:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"Expected list '{key}'.")
    return value


def _required_string_list(payload: dict, key: str) -> list[str]:
    values = _required_list(payload, key)
    if not all(isinstance(value, str) and value for value in values):
        raise ValueError(f"Expected non-empty string values in '{key}'.")
    return values


def main() -> int:
    """Run the deterministic Agent tool-boundary benchmark without external side effects."""
    report = run_tool_simulator_benchmark()
    print(json.dumps(report.to_dict(), ensure_ascii=False))
    return 0 if report.detection_rate == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
