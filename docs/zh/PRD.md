# 产品需求文档

## 1. 项目来源

Human-Centred AI Driving Coach 的灵感来自研究生阶段的两门课程：Human Factors，以及 Ethics, Safety and Regulation。

在 Human Factors 课程项目中，我们研究了 lane keeping 功能对驾驶员心理状态和驾驶状态的影响。这个项目引出了一个更大的产品问题：

> 驾驶表现能否被量化？能否通过车辆行为、路线场景和可选驾驶状态信号，帮助驾驶者或评估者理解并改进下一次驾驶？

因此，DriveCoach AI 不只是一个 telemetry dashboard，而是一个 post-drive AI coaching product。它关注的是：行程结束后，系统如何把原始车辆数据转化为驾驶行为洞察、路线相关的 Risk Event 解释，以及可衡量的下一次驾驶目标。

## 2. 一句话定位

DriveCoach AI 是一款 route-aware post-drive AI coaching product，把 connected-vehicle telemetry 转化为 evidence-grounded driving behaviour insights 和 measurable next-drive targets。

## 3. 目标用户

### ADAS / Intelligent Driving Evaluator

需要解释某次驾驶或仿真 session 中车辆和驾驶者在不同路段的表现，关注证据、可复现性、路线场景和前后对比。

### 驾驶者 / 学习者

不想阅读原始 telemetry，希望看到清晰、具体、可执行的驾驶改进建议。

### Human Factors / Safety Research Student

希望把驾驶行为、ADAS 使用前后变化和可选 driver-state context 结合起来，形成可解释的研究型产品原型。

## 4. 核心问题

当前不是缺少数据，而是缺少把数据转化为可执行 coaching 的产品层。

原始 speed、ax、ay、yawRate 可以描述车辆运动，但用户真正需要知道的是：

- 这次驾驶整体表现如何？
- 主要问题发生在哪类路段？
- 证据是什么？
- 为什么会影响 comfort、stability 或 predictability？
- 下一次应该具体改什么？
- 和上一次相比有没有进步？

## 5. 用户痛点

1. 原始 telemetry 准确但难以理解。
2. Risk Event 如果没有路线场景，解释价值有限。
3. AI 建议容易变成泛泛而谈。
4. 用户需要一个清晰的 next-drive focus，而不是一份长报告。
5. ADAS-on/off 对比需要历史记忆和可控变量。
6. 心率等 wearable data 容易被误解，因此必须保持可选和非医疗化表达。

## 6. 产品链路

```text
Regenerate Sample Trip
-> Generate route-grounded driving session
-> Calculate deterministic metrics
-> Detect context-aware Risk Events
-> Run AI coach workflow
-> Show Summary / Drive Data / Coach / History
-> Save session memory
-> Compare next session with previous target
```

## 7. 信息架构

| 区域 | 作用 |
| --- | --- |
| Landing / Demo | 说明产品定位，选择测试场景，生成示例行程 |
| Summary | 快速回答这次驾驶整体如何 |
| Drive Data | 展示速度、加速度、路线和可选 wearable evidence |
| Coach | 输出主结论、关键证据、下一次目标和 Ask DriveCoach |
| History | 展示 score trend、上次对比和 repeated pattern |
| Evidence & trust | 折叠展示 retrieved knowledge、evaluation、trace 等工程可信信息 |

## 8. 功能优先级

### P0

- 生成 route-grounded sample trip
- deterministic metrics
- context-aware Risk Event detection
- Summary / Drive Data / Coach / History
- 前端无 CSV upload
- backend / LLM 不可用时仍可 fallback
- 明确标注 synthetic data

### P1

- Ask DriveCoach
- RAG-lite knowledge
- LangGraph workflow
- validation and revision loop
- SQLite session memory
- target completion loop
- agent quality evaluation
- 中英文 UI 和文档

### P2

- OSRM / OSMnx real route fetching
- CARLA / ROS bag / CAN-derived telemetry ingestion
- ADAS-on/off comparison
- vector RAG
- report export
- deployment and authentication

## 9. MVP 成功标准

- 用户一分钟内能理解这是 post-drive AI coaching product。
- 不上传 CSV 也能完成完整 demo flow。
- Summary 能看到路线、评分和主要风险点。
- Coach 能说明 overall assessment、main pattern、route context、why it matters 和 next-drive focus。
- 用户可以展开 Evidence & trust 查看证据。
- History 能展示趋势和目标完成情况。
- 无医疗、疲劳、压力诊断等过度声明。

## 10. 原型说明

当前原型采用单页 Next.js demo 和 iPhone-style review surface。这样既能表达面向用户的 session review，又能保留背后的 engineering credibility。

设计原则：

- 默认界面不要像工程 dashboard。
- 先给结论，再给证据。
- 技术可信信息默认收起。
- route context 用地图表达。
- Coach tab 只保留最关键的 summary、evidence、target 和 chat。
