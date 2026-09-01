## Why

当前 AQE 只对内置的确定性 Fixture 运行门禁，能够证明规则本身，却不能证明它能安全地评估一个真实 RAG 服务。仓库内已有本地可启动的 StuckToShip（EduRAG）服务：它稳定暴露问答、引用和 Trace 契约，并自带可回归的课程问答评测集，因此适合作为第一个真实靶场。

## What Changes

- 新增一个只读的 StuckToShip HTTP 适配器，将目标服务的问答响应归一为 AQE 证据输入。
- 新增目标专属的 RAG 评测集，验证可回答问题的引用、预期路由，以及模糊问题的澄清行为。
- 新增一个显式的本地执行入口；目标地址和 API Key 仅从调用者参数或环境变量读取，绝不持久化、记录或暴露为通用 API。
- 保持既有 Fixture 门禁、Benchmark API 和 CI 自检不变。

## Capabilities

### New Capabilities

- `stucktoship-rag-adapter`: 以受控、只读的 HTTP 调用连接 StuckToShip RAG 服务，并归一化回答、引用、路由和 Trace。
- `stucktoship-rag-evaluation`: 使用可重复的目标专属案例产出 pass、block 或 escalate 证据，而非把真实服务的网络或契约错误伪装为通过。

### Modified Capabilities

无。

## Impact

- 新增 `aqe` 中的 HTTP 适配器、目标专属数据集和可执行运行器。
- 新增单元/契约测试；真实本地冒烟只调用 `http://127.0.0.1` 的既有 EduRAG 服务。
- 不新增数据库表、前端页面或第三方依赖；HTTP 调用使用现有项目依赖。
