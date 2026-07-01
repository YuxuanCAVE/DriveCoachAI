# DriveCoach AI Documentation

This folder contains the core product, technical, agent, and evaluation documentation for DriveCoach AI.

Recommended reading order:

1. [PRD](PRD.md)
2. [Technical Design](TECHNICAL_DESIGN.md)
3. [Agent Workflow Design](AGENT_WORKFLOW_DESIGN.md)
4. [Metrics and Evaluation](METRICS_AND_EVALUATION.md)

## Document Map

| Document | Audience | Purpose |
| --- | --- | --- |
| [PRD](PRD.md) | Product reviewers, project evaluators, designers, engineers | Explains the product origin, target users, user journey, MVP scope, product value, and roadmap |
| [Technical Design](TECHNICAL_DESIGN.md) | Engineers and technical reviewers | Explains the frontend, backend, API surface, data contract, session generation, fallback strategy, and system architecture |
| [Agent Workflow Design](AGENT_WORKFLOW_DESIGN.md) | AI engineers and agent reviewers | Explains the coach agent state, LangGraph-ready workflow, retrieval, report generation, validation, and revision loop |
| [Metrics and Evaluation](METRICS_AND_EVALUATION.md) | Analytics, evaluation, and safety reviewers | Explains metric formulas, risk-event rules, context-aware thresholds, calibration plan, report evaluation, and knowledge evaluation |

## Project Narrative

DriveCoach AI is a post-drive coaching product for connected-vehicle telemetry and ADAS-oriented driver behaviour review.

The product flow is:

```text
Trip or demo session
-> deterministic telemetry analysis
-> route-aware risk-event detection
-> evidence-grounded AI coaching
-> measurable next-drive target
-> lightweight history comparison
```

The central design principle is:

> The system calculates evidence deterministically, then uses the AI coach to explain that evidence in practical, route-aware language.

## Current MVP Scope

The current implementation demonstrates:

- route-grounded synthetic sessions for Cranfield University to Milton Keynes Midsummer Place
- deterministic metrics and context-aware event detection
- iPhone-style Next.js product demo
- FastAPI backend bridge
- optional DeepSeek LLM integration
- deterministic fallback when LLM or backend is unavailable
- RAG-lite knowledge retrieval
- LangGraph-compatible agent workflow
- validation and revision loop
- SQLite session memory
- target completion
- report and knowledge evaluation

## What This Project Is Not

DriveCoach AI is not:

- a real-time in-car warning system
- a medical or fatigue diagnosis system
- an insurance scoring system
- a production ADAS safety certification tool
- a replacement for driver responsibility

The current data is synthetic and route-grounded. It should be treated as a product and engineering prototype until real telemetry calibration is completed.

## Useful Entry Points

For a product review:

1. Read [PRD](PRD.md).
2. Open the local demo.
3. Review the Summary, Drive Data, Coach, and History tabs.
4. Read the MVP success criteria and product boundaries.

For a technical review:

1. Read [Technical Design](TECHNICAL_DESIGN.md).
2. Inspect `backend/main.py`.
3. Inspect `backend/services/demo_session_service.py`.
4. Inspect `src/lib/apiClient.ts`.
5. Run the verification commands in the root README.

For an AI-agent review:

1. Read [Agent Workflow Design](AGENT_WORKFLOW_DESIGN.md).
2. Inspect `backend/agent/coach_workflow.py`.
3. Inspect `backend/agent/langgraph_workflow.py`.
4. Inspect `backend/evaluation/report_evaluator.py`.
5. Inspect `backend/knowledge/*.md`.

For metrics and evaluation:

1. Read [Metrics and Evaluation](METRICS_AND_EVALUATION.md).
2. Review the context-aware threshold model.
3. Review the calibration plan.
4. Review agent report and knowledge evaluation gates.

