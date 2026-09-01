from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from aqe.tool_simulator import ToolCall, ToolDefinition, ToolGateEvidence, run_tool_gate


class AgentTraceContractError(ValueError):
    pass


@dataclass(frozen=True)
class TracedToolCall:
    call: ToolCall
    message_index: int
    has_result: bool


@dataclass(frozen=True)
class AgentTrace:
    calls: tuple[TracedToolCall, ...]


@dataclass(frozen=True)
class AgentTraceGateEvidence:
    tool_evidence: ToolGateEvidence
    source_message_indexes: tuple[int, ...]


def normalize_langgraph_trace(messages: Sequence[Mapping[str, object]]) -> AgentTrace:
    calls: list[TracedToolCall] = []
    result_names = {
        str(message.get("name"))
        for message in messages
        if message.get("type") == "tool" and isinstance(message.get("name"), str)
    }
    for message_index, message in enumerate(messages):
        raw_calls = message.get("tool_calls")
        if raw_calls is None:
            continue
        if not isinstance(raw_calls, list):
            raise AgentTraceContractError("tool_calls must be a list.")
        for raw_call in raw_calls:
            if not isinstance(raw_call, Mapping):
                raise AgentTraceContractError("tool_calls entries must be objects.")
            name = raw_call.get("name")
            arguments = raw_call.get("args", raw_call.get("arguments"))
            if not isinstance(name, str) or not name:
                raise AgentTraceContractError("tool call name must be a non-empty string.")
            if not isinstance(arguments, Mapping):
                raise AgentTraceContractError("tool call arguments must be an object.")
            calls.append(
                TracedToolCall(ToolCall(name, dict(arguments)), message_index, name in result_names)
            )
    return AgentTrace(tuple(calls))


def evaluate_langgraph_trace(
    messages: Sequence[Mapping[str, object]],
    *,
    tools: tuple[ToolDefinition, ...],
    role: str,
) -> AgentTraceGateEvidence:
    trace = normalize_langgraph_trace(messages)
    tool_evidence = run_tool_gate(tools, role=role, calls=tuple(item.call for item in trace.calls))
    return AgentTraceGateEvidence(
        tool_evidence=tool_evidence,
        source_message_indexes=tuple(item.message_index for item in trace.calls),
    )
