## ADDED Requirements

### Requirement: Read-only LangGraph tool trace normalization
The system SHALL normalize mapping-shaped LangGraph assistant tool calls and tool-result messages into ordered AQE tool calls without importing an Agent runtime or executing a tool.

#### Scenario: Assistant tool call and result are normalized
- **WHEN** a trace contains an assistant message with `{name, args}` and a following `type="tool"` message
- **THEN** AQE preserves the tool name, arguments and source message position for policy evaluation

#### Scenario: Malformed tool call is explicit
- **WHEN** a declared tool call lacks a non-empty name or object arguments
- **THEN** the adapter returns a structured contract error and does not silently omit that call
