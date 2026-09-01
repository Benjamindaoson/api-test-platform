from __future__ import annotations

import pytest


def test_langgraph_trace_normalizes_real_tool_call_shape_and_preserves_message_position():
    from aqe.agent_trace import normalize_langgraph_trace

    trace = normalize_langgraph_trace(
        [
            {"type": "human", "content": "research RAG"},
            {"type": "ai", "tool_calls": [{"name": "web_search", "args": {"query": "RAG"}}]},
            {"type": "tool", "name": "web_search", "content": "result"},
        ]
    )

    assert trace.calls[0].call.tool_name == "web_search"
    assert trace.calls[0].message_index == 1
    assert trace.calls[0].has_result is True


def test_langgraph_trace_rejects_malformed_declared_tool_calls():
    from aqe.agent_trace import AgentTraceContractError, normalize_langgraph_trace

    with pytest.raises(AgentTraceContractError, match="arguments"):
        normalize_langgraph_trace([{"type": "ai", "tool_calls": [{"name": "web_search", "args": "bad"}]}])


def test_agent_trace_gate_keeps_source_message_position_for_policy_failure():
    from aqe.agent_trace import evaluate_langgraph_trace
    from aqe.tool_simulator import ToolDefinition

    evidence = evaluate_langgraph_trace(
        [{"type": "ai", "tool_calls": [{"name": "delete_customer", "args": {"id": "1"}}]}],
        tools=(ToolDefinition("search_docs", ("query",)),),
        role="researcher",
    )

    assert evidence.tool_evidence.rule_ids == ("tool-unknown",)
    assert evidence.source_message_indexes == (0,)
