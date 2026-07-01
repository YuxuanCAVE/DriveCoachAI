# DriveCoach AI 中文文档

本目录是 DriveCoach AI / Human-Centred AI Driving Coach 的中文文档入口，适合中文答辩、项目展示和产品说明。

推荐阅读顺序：

1. [产品需求文档](PRD.md)
2. [技术设计](TECHNICAL_DESIGN.md)
3. [Agent 工作流设计](AGENT_WORKFLOW_DESIGN.md)
4. [指标与评估](METRICS_AND_EVALUATION.md)

## 项目一句话

DriveCoach AI 是一款行程结束后的 AI 驾驶教练产品，把 connected-vehicle telemetry、路线场景和可选驾驶状态信号转化为可解释的驾驶行为洞察、Risk Event 说明和下一次驾驶改进目标。

## 当前 MVP

当前版本已经包含：

- Next.js / TypeScript 前端 demo
- FastAPI 后端
- Cranfield University 到 Milton Keynes Midsummer Place 的路线场景
- route-grounded synthetic session
- deterministic metrics
- context-aware Risk Event detection
- AI Coach summary 和 Ask DriveCoach 对话
- RAG-lite 知识库
- LangGraph-ready workflow
- SQLite session memory
- target completion loop
- agent quality evaluation
- 中英文前端 UI

## 产品边界

DriveCoach AI 不是：

- 实时车内预警系统
- 医疗或疲劳诊断系统
- 保险评分系统
- 事故责任判定工具
- ADAS 安全认证工具

当前数据是 route-grounded synthetic data，不是真实驾驶员数据。车辆遥测是核心分析来源，心率或穿戴数据只作为可选上下文。

## 英文文档

英文版位于 [`../en/`](../en/README.md)，GitHub README 默认以英文为主。
