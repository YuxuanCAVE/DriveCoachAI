from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DB_PATH = PROJECT_ROOT / "data" / "session_memory.sqlite"


def connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            stored_at TEXT NOT NULL,
            scenario_key TEXT,
            scenario_label TEXT,
            seed INTEGER,
            overall_score REAL,
            longitudinal_score REAL,
            lateral_score REAL,
            context_score REAL,
            risk_event_count INTEGER,
            max_abs_ax REAL,
            max_abs_ay REAL,
            trip_json TEXT NOT NULL
        )
        """
    )
    return conn


def event_count(trip: dict[str, Any], event_type: str) -> int:
    return len([event for event in trip.get("events", []) if event.get("type") == event_type])


def trip_record(trip: dict[str, Any]) -> dict[str, Any]:
    metrics = trip.get("metrics", {})
    scenario = trip.get("scenario", {})
    return {
        "id": trip.get("id"),
        "created_at": trip.get("createdAt") or datetime.now(timezone.utc).isoformat(),
        "stored_at": datetime.now(timezone.utc).isoformat(),
        "scenario_key": scenario.get("key"),
        "scenario_label": scenario.get("label"),
        "seed": scenario.get("seed"),
        "overall_score": metrics.get("overallDrivingScore"),
        "longitudinal_score": metrics.get("longitudinalSmoothnessScore"),
        "lateral_score": metrics.get("lateralStabilityScore"),
        "context_score": metrics.get("contextAdaptationScore"),
        "risk_event_count": metrics.get("riskEventCount"),
        "max_abs_ax": metrics.get("maxAbsAx"),
        "max_abs_ay": metrics.get("maxAbsAy"),
        "trip_json": json.dumps(trip),
    }


def save_session(trip: dict[str, Any]) -> None:
    record = trip_record(trip)
    with connection() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO sessions (
                id, created_at, stored_at, scenario_key, scenario_label, seed,
                overall_score, longitudinal_score, lateral_score, context_score,
                risk_event_count, max_abs_ax, max_abs_ay, trip_json
            ) VALUES (
                :id, :created_at, :stored_at, :scenario_key, :scenario_label, :seed,
                :overall_score, :longitudinal_score, :lateral_score, :context_score,
                :risk_event_count, :max_abs_ax, :max_abs_ay, :trip_json
            )
            """,
            record,
        )


def recent_sessions(limit: int = 8) -> list[dict[str, Any]]:
    with connection() as conn:
        rows = conn.execute(
            """
            SELECT id, created_at, stored_at, scenario_key, scenario_label, seed,
                   overall_score, longitudinal_score, lateral_score, context_score,
                   risk_event_count, max_abs_ax, max_abs_ay
            FROM sessions
            ORDER BY stored_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def recent_session_trips(limit: int = 5, exclude_id: str | None = None) -> list[dict[str, Any]]:
    query = """
        SELECT trip_json
        FROM sessions
        {where_clause}
        ORDER BY stored_at DESC
        LIMIT ?
    """
    where_clause = "WHERE id != ?" if exclude_id else ""
    params: tuple[Any, ...] = (exclude_id, limit) if exclude_id else (limit,)
    with connection() as conn:
        rows = conn.execute(query.format(where_clause=where_clause), params).fetchall()
    return [json.loads(row["trip_json"]) for row in rows]


def previous_session(current_id: str) -> dict[str, Any] | None:
    with connection() as conn:
        row = conn.execute(
            """
            SELECT trip_json
            FROM sessions
            WHERE id != ?
            ORDER BY stored_at DESC
            LIMIT 1
            """,
            (current_id,),
        ).fetchone()
    return json.loads(row["trip_json"]) if row else None


def delta(current: float | int | None, previous: float | int | None) -> float | None:
    if current is None or previous is None:
        return None
    return float(current) - float(previous)


def direction(delta_value: float | None, higher_is_better: bool = True) -> str:
    if delta_value is None or abs(delta_value) < 0.05:
        return "unchanged"
    improved = delta_value > 0 if higher_is_better else delta_value < 0
    return "improved" if improved else "declined"


def compare_sessions(current_trip: dict[str, Any], previous_trip: dict[str, Any] | None) -> dict[str, Any]:
    current_metrics = current_trip.get("metrics", {})
    if previous_trip is None:
        return {
            "hasPrevious": False,
            "currentSessionId": current_trip.get("id"),
            "previousSessionId": None,
            "insights": ["No previous session is stored yet. This trip becomes the baseline for future comparisons."],
            "deltas": {},
        }

    previous_metrics = previous_trip.get("metrics", {})
    score_delta = delta(current_metrics.get("overallDrivingScore"), previous_metrics.get("overallDrivingScore"))
    longitudinal_delta = delta(current_metrics.get("longitudinalSmoothnessScore"), previous_metrics.get("longitudinalSmoothnessScore"))
    lateral_delta = delta(current_metrics.get("lateralStabilityScore"), previous_metrics.get("lateralStabilityScore"))
    risk_delta = delta(current_metrics.get("riskEventCount"), previous_metrics.get("riskEventCount"))
    max_ax_delta = delta(current_metrics.get("maxAbsAx"), previous_metrics.get("maxAbsAx"))
    max_ay_delta = delta(current_metrics.get("maxAbsAy"), previous_metrics.get("maxAbsAy"))

    current_late_braking = event_count(current_trip, "late_braking_before_curve") + event_count(current_trip, "harsh_braking")
    previous_late_braking = event_count(previous_trip, "late_braking_before_curve") + event_count(previous_trip, "harsh_braking")
    braking_event_delta = current_late_braking - previous_late_braking

    insights: list[str] = []
    if score_delta is not None:
        if score_delta > 1:
            insights.append(f"Overall driving score improved by {score_delta:.1f} points compared with the previous stored session.")
        elif score_delta < -1:
            insights.append(f"Overall driving score decreased by {abs(score_delta):.1f} points compared with the previous stored session.")
        else:
            insights.append("Overall driving score stayed broadly similar to the previous stored session.")

    if longitudinal_delta is not None and max_ax_delta is not None:
        if longitudinal_delta > 1 and max_ax_delta < 0:
            insights.append("Braking and acceleration were smoother than the previous session, with lower peak longitudinal demand.")
        elif longitudinal_delta < -1 or max_ax_delta > 0.2:
            insights.append("Longitudinal control was less smooth than the previous session, so braking and throttle transitions are the main review area.")

    if lateral_delta is not None and max_ay_delta is not None:
        if lateral_delta > 1 and max_ay_delta < 0:
            insights.append("Cornering stability improved, with lower peak lateral demand than the previous session.")
        elif lateral_delta < -1 or max_ay_delta > 0.2:
            insights.append("Lateral stability declined compared with the previous session, likely around higher-demand bends or junction context.")

    if risk_delta is not None:
        if risk_delta < 0:
            insights.append(f"Detected risk events decreased by {abs(int(risk_delta))}.")
        elif risk_delta > 0:
            insights.append(f"Detected risk events increased by {int(risk_delta)}.")

    if braking_event_delta < 0:
        insights.append("Late or harsh braking events decreased compared with the previous session.")
    elif braking_event_delta > 0:
        insights.append("Late or harsh braking events increased compared with the previous session.")

    return {
        "hasPrevious": True,
        "currentSessionId": current_trip.get("id"),
        "previousSessionId": previous_trip.get("id"),
        "previousScenario": previous_trip.get("scenario", {}).get("label"),
        "insights": insights[:4] or ["This session is broadly similar to the previous stored session."],
        "deltas": {
            "overallDrivingScore": {"value": score_delta, "direction": direction(score_delta)},
            "longitudinalSmoothnessScore": {"value": longitudinal_delta, "direction": direction(longitudinal_delta)},
            "lateralStabilityScore": {"value": lateral_delta, "direction": direction(lateral_delta)},
            "riskEventCount": {"value": risk_delta, "direction": direction(risk_delta, higher_is_better=False)},
            "maxAbsAx": {"value": max_ax_delta, "direction": direction(max_ax_delta, higher_is_better=False)},
            "maxAbsAy": {"value": max_ay_delta, "direction": direction(max_ay_delta, higher_is_better=False)},
            "brakingEventCount": {"value": braking_event_delta, "direction": direction(braking_event_delta, higher_is_better=False)},
        },
    }


def compare_and_optionally_save(trip: dict[str, Any], save: bool = True) -> dict[str, Any]:
    previous = previous_session(str(trip.get("id")))
    comparison = compare_sessions(trip, previous)
    if save:
        save_session(trip)
    comparison["recentSessions"] = recent_sessions()
    return comparison
