from __future__ import annotations


def test_tool_simulator_blocks_permission_timeout_and_duplicate_calls():
    from aqe.tool_simulator import ToolCall, ToolDefinition, run_tool_gate

    tools = (
        ToolDefinition(name="search_docs", required_arguments=("query",), allowed_roles=("researcher",)),
        ToolDefinition(name="fetch_status", required_arguments=("ticket",), behavior="timeout"),
    )

    evidence = run_tool_gate(
        tools,
        role="viewer",
        calls=(
            ToolCall("search_docs", {"query": "RAG"}),
            ToolCall("fetch_status", {"ticket": "AQE-1"}),
            ToolCall("fetch_status", {"ticket": "AQE-1"}),
        ),
    )

    assert evidence.verdict == "block"
    assert evidence.rule_ids == ("tool-permission", "tool-timeout", "tool-duplicate")


def test_versioned_tool_simulator_corpus_detects_all_injected_failures():
    from aqe.tool_simulator import run_tool_simulator_benchmark

    report = run_tool_simulator_benchmark()

    assert report.version == "agent-tool-simulator-v1"
    assert report.detection_rate == 1.0
    assert report.detected_scenarios == report.total_scenarios == 5
    assert {scenario.expected_rule_id for scenario in report.scenarios} == {
        "tool-unknown",
        "tool-arguments",
        "tool-permission",
        "tool-timeout",
        "tool-duplicate",
    }
