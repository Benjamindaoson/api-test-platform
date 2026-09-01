## Context

AQE 的现有 `run_release_gate` 只执行内置 Fixture，不能验证真实服务的 HTTP 契约或真实检索、引用和路由。StuckToShip（EduRAG）在本机可用 `POST /api/v1/rag/ask`，请求为 `{query, stream, session_id}`，成功响应为 `{code: 0, data: {answer, references, route, trace}}`。它已有覆盖 course、code、error、faq、learning_path 和 clarify 的 32 条评测集。

本次接入是一个受控的本地/CI 执行器，而不是向 API 测试平台新增一个可提交任意 URL 的管理端点。

## Goals / Non-Goals

**Goals:**

- 用一个可注入的 HTTP transport 调用 StuckToShip 的非流式问答接口。
- 对返回的回答、引用、路由和 Trace 做严格契约校验并生成结构化 AQE 证据。
- 以四个稳定、跨路由的案例检测真实服务的关键回归：课程回答、代码定位、FAQ 配置和模糊问题澄清。
- 将不可达目标、HTTP 错误或响应契约错误判为 `escalate`，而不是 `pass` 或 `block`。
- 提供命令行入口，目标地址和 Key 只从本地参数/环境变量读取。

**Non-Goals:**

- 不把任意目标 URL 暴露为 FastAPI 管理 API；不引入 SSRF 风险。
- 不上传/删除 EduRAG 知识、不会触发建索引、不写入其数据库。
- 不声称该四例集合是人类测试工程师基准，也不替代 RAGAS 或事故回放。
- 不修改既有 Fixture Gate、其 Benchmark 或公开 API。

## Decisions

### 1. 新增目标专属执行器，不扩展 Fixture 的故障档位

`aqe/stucktoship.py` 负责网络调用与契约归一，`aqe/stucktoship_gate.py` 负责评估与证据判定。真实目标与故障注入 Fixture 的数据语义不同；强行复用 `FixtureResponse` 会错误要求固定文本和固定文档 ID。保持两条执行路径可避免削弱现有确定性门禁。

备选方案是改造现有 `run_release_gate` 支持所有 provider。该方案会把固定引用集合、protected marker 等 Fixture 专属规则扩散到真实目标，当前不采用。

### 2. 以明确、只读的命令行入口执行

`python -m aqe.stucktoship_gate` 接受 `--base-url`；未提供时读取 `AQE_STUCKTOSHIP_BASE_URL`，再回退到 `http://127.0.0.1:8010`。可选 Authorization 值仅从 `AQE_STUCKTOSHIP_API_KEY` 读取，且不得写入返回证据、日志或异常文本。调用固定为 `POST /api/v1/rag/ask` 与 `stream: false`。

备选方案是新增 `/api/aqe/targets/run`。该方式需要 URL allowlist、DNS/IP 重绑定防护、凭据管理与 RBAC；留到平台具备多租户安全边界后再做。

### 3. 证据规则以目标契约为中心

评测案例要求精确路由和最小的、案例专属的答案断言；可回答问题必须有至少一个非空引用，澄清问题必须返回 `route=clarify` 且 Trace 决策为 `clarify`。返回 `code != 0`、缺少必填字段或网络错误是“验证受阻”（`escalate`）；已收到有效响应但违反案例规则才是 `block`。

备选方案是只检查回答包含关键词。该方式容易把无引用的幻觉答案判为通过，因此不采用。

### 4. 传输层依赖注入，生产默认使用标准库

适配器接收一个可替换的 request callable；生产默认使用 `urllib.request`，不增加新依赖。单元测试使用可控 transport，验证真实序列化和响应解析，而不依赖本机服务。

## Risks / Trade-offs

- [目标知识库或路由规则变化导致用例阻断] → 将数据集独立版本化；先从 StuckToShip 已有评测语料挑选稳定问题。
- [服务依赖模型/索引无法启动] → 冒烟命令报告 `escalate` 与原因；不将基础设施失败误报成模型质量问题。
- [日志意外泄露 API Key] → 适配器只在 header 内使用 Key，错误信息只报告状态、路径和安全摘要。
- [四例覆盖不足] → 证据显式标记为 `stucktoship-rag-v1`；下一阶段从 32 条评测集和历史事故扩展。

## Migration Plan

1. 保留现有 AQE Fixture/Benchmark 不变，新增独立模块、数据集、测试和 CLI。
2. 在本地启动 EduRAG 后执行真实冒烟，记录其结构化证据但不提交运行产生的目标数据。
3. 在未来 CI 可启动目标服务后，将 CLI 接到目标仓库变更工作流；回滚时移除调用步骤即可，现有 Fixture 门禁不受影响。
