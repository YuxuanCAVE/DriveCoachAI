from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "agent_observability.sqlite"


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_traces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            session_id TEXT,
            scenario_key TEXT,
            agent_mode TEXT,
            workflow_engine TEXT,
            workflow_nodes_json TEXT NOT NULL,
            duration_ms INTEGER,
            quality_score INTEGER,
            evaluation_passed INTEGER NOT NULL,
            risk_event_count INTEGER,
            retrieved_knowledge_count INTEGER,
            compact_trace_json TEXT NOT NULL
        )
        """
    )
    return connection


def _compact_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": event.get("id"),
            "type": event.get("type"),
            "severity": event.get("severity"),
            "segmentName": event.get("segmentName"),
            "startTime": event.get("startTime"),
            "endTime": event.get("endTime"),
        }
        for event in events[:8]
    ]


def build_compact_trace(report: dict[str, Any], trip: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
    metrics = trip.get("metrics", {})
    scenario = trip.get("scenario", {})
    return {
        "sessionId": trip.get("id"),
        "scenario": {
            "key": scenario.get("key"),
            "label": scenario.get("label"),
            "seed": scenario.get("seed"),
            "generationMode": scenario.get("generationMode"),
        },
        "route": trip.get("route", {}),
        "metrics": {
            "overallDrivingScore": metrics.get("overallDrivingScore"),
            "contextAdaptationScore": metrics.get("contextAdaptationScore"),
            "riskEventCount": metrics.get("riskEventCount"),
            "wearableConnected": metrics.get("wearableConnected"),
        },
        "events": _compact_events(trip.get("events", [])),
        "agent": {
            "agentMode": report.get("agentMode"),
            "llmProvider": report.get("llmProvider"),
            "llmModel": report.get("llmModel"),
            "workflowEngine": report.get("workflowEngine"),
            "workflowNodes": report.get("workflowNodes", []),
            "fallbackReason": report.get("workflowFallbackReason") or report.get("llmFallbackReason"),
        },
        "retrievedKnowledge": report.get("retrievedKnowledge", []),
        "evidenceUsed": report.get("evidenceUsed", []),
        "evaluation": evaluation,
    }


def record_agent_trace(report: dict[str, Any], trip: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
    compact_trace = build_compact_trace(report, trip, evaluation)
    scenario = trip.get("scenario", {})
    metrics = trip.get("metrics", {})
    created_at = datetime.now(timezone.utc).isoformat()

    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO agent_traces (
                created_at, session_id, scenario_key, agent_mode, workflow_engine, workflow_nodes_json,
                duration_ms, quality_score, evaluation_passed, risk_event_count, retrieved_knowledge_count,
                compact_trace_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                created_at,
                trip.get("id"),
                scenario.get("key"),
                report.get("agentMode"),
                report.get("workflowEngine"),
                json.dumps(report.get("workflowNodes", []), ensure_ascii=False),
                evaluation.get("durationMs"),
                evaluation.get("qualityScore"),
                1 if evaluation.get("passed") else 0,
                metrics.get("riskEventCount", len(trip.get("events", []))),
                len(report.get("retrievedKnowledge", [])),
                json.dumps(compact_trace, ensure_ascii=False),
            ),
        )
        trace_id = int(cursor.lastrowid)

    return {
        "traceId": trace_id,
        "createdAt": created_at,
        "sessionId": trip.get("id"),
        "qualityScore": evaluation.get("qualityScore"),
        "evaluationPassed": evaluation.get("passed"),
    }


def recent_agent_traces(limit: int = 10) -> list[dict[str, Any]]:
    safe_limit = max(1, min(limit, 50))
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, created_at, session_id, scenario_key, agent_mode, workflow_engine, workflow_nodes_json,
                   duration_ms, quality_score, evaluation_passed, risk_event_count, retrieved_knowledge_count,
                   compact_trace_json
            FROM agent_traces
            ORDER BY id DESC
            LIMIT ?
            """,
            (safe_limit,),
        ).fetchall()

    traces: list[dict[str, Any]] = []
    for row in rows:
        compact_trace = json.loads(row["compact_trace_json"])
        traces.append(
            {
                "traceId": row["id"],
                "createdAt": row["created_at"],
                "sessionId": row["session_id"],
                "scenarioKey": row["scenario_key"],
                "agentMode": row["agent_mode"],
                "workflowEngine": row["workflow_engine"],
                "workflowNodes": json.loads(row["workflow_nodes_json"]),
                "durationMs": row["duration_ms"],
                "qualityScore": row["quality_score"],
                "evaluationPassed": bool(row["evaluation_passed"]),
                "riskEventCount": row["risk_event_count"],
                "retrievedKnowledgeCount": row["retrieved_knowledge_count"],
                "evaluation": compact_trace.get("evaluation", {}),
                "compactTrace": compact_trace,
            }
        )
    return traces

