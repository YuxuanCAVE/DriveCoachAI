from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.services.session_memory_service import compare_sessions, previous_session, recent_session_trips, recent_sessions


PATTERNS = [
    {
        "id": "late_braking_pattern",
        "eventTypes": {"late_braking_before_curve", "harsh_braking"},
        "label": "late or firm braking before higher-demand sections",
        "watchItem": "Keep braking earlier and more progressive before rural bends, village approaches, and junctions.",
    },
    {
        "id": "cornering_demand_pattern",
        "eventTypes": {"high_lateral_acceleration", "unstable_cornering", "high_speed_in_curve", "sharp_yaw_motion"},
        "label": "higher cornering demand around curve or junction context",
        "watchItem": "Keep lowering entry speed before high-curvature route sections.",
    },
    {
        "id": "speed_control_pattern",
        "eventTypes": {"unstable_speed_control", "harsh_acceleration"},
        "label": "speed fluctuation during urban or stop-go sections",
        "watchItem": "Keep throttle and brake transitions smoother during urban arrival.",
    },
]


def _metric(trip: dict[str, Any], key: str) -> float:
    value = trip.get("metrics", {}).get(key)
    return float(value) if isinstance(value, int | float) else 0.0


def _event_types(trip: dict[str, Any]) -> set[str]:
    return {str(event.get("type", "")) for event in trip.get("events", [])}


def _has_pattern(trip: dict[str, Any], event_types: set[str]) -> bool:
    return bool(_event_types(trip).intersection(event_types))


def _score_point_from_record(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "sessionId": record.get("id"),
        "label": record.get("scenario_label") or record.get("scenario_key") or "Stored session",
        "storedAt": record.get("stored_at"),
        "overallScore": record.get("overall_score"),
        "longitudinalScore": record.get("longitudinal_score"),
        "lateralScore": record.get("lateral_score"),
        "riskEventCount": record.get("risk_event_count"),
        "isCurrent": False,
    }


def _score_point_from_trip(trip: dict[str, Any]) -> dict[str, Any]:
    scenario = trip.get("scenario", {})
    metrics = trip.get("metrics", {})
    return {
        "sessionId": trip.get("id"),
        "label": scenario.get("label") or scenario.get("key") or "Current session",
        "storedAt": trip.get("createdAt") or datetime.now(timezone.utc).isoformat(),
        "overallScore": metrics.get("overallDrivingScore"),
        "longitudinalScore": metrics.get("longitudinalSmoothnessScore"),
        "lateralScore": metrics.get("lateralStabilityScore"),
        "riskEventCount": metrics.get("riskEventCount"),
        "isCurrent": True,
    }


def _score_trend(current_trip: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    current_id = str(current_trip.get("id"))
    records = [record for record in recent_sessions(limit=limit) if record.get("id") != current_id]
    points = [_score_point_from_record(record) for record in reversed(records[-max(0, limit - 1) :])]
    points.append(_score_point_from_trip(current_trip))
    return points[-limit:]


def _improvements(comparison: dict[str, Any]) -> list[str]:
    deltas = comparison.get("deltas", {})
    output: list[str] = []
    if deltas.get("overallDrivingScore", {}).get("direction") == "improved":
        value = deltas["overallDrivingScore"].get("value")
        output.append(f"Overall driving score improved by {value:.1f} points compared with the previous stored session.")
    if deltas.get("riskEventCount", {}).get("direction") == "improved":
        value = abs(int(deltas["riskEventCount"].get("value", 0)))
        output.append(f"Detected risk events decreased by {value}.")
    if deltas.get("brakingEventCount", {}).get("direction") == "improved":
        output.append("Late or harsh braking events decreased versus the previous stored session.")
    if deltas.get("lateralStabilityScore", {}).get("direction") == "improved":
        output.append("Lateral stability score improved compared with the previous stored session.")
    return output[:3]


def _declines(comparison: dict[str, Any]) -> list[str]:
    deltas = comparison.get("deltas", {})
    output: list[str] = []
    if deltas.get("overallDrivingScore", {}).get("direction") == "declined":
        value = abs(float(deltas["overallDrivingScore"].get("value", 0)))
        output.append(f"Overall driving score decreased by {value:.1f} points versus the previous stored session.")
    if deltas.get("riskEventCount", {}).get("direction") == "declined":
        value = int(deltas["riskEventCount"].get("value", 0))
        output.append(f"Detected risk events increased by {value}.")
    if deltas.get("brakingEventCount", {}).get("direction") == "declined":
        output.append("Late or harsh braking events increased versus the previous stored session.")
    if deltas.get("lateralStabilityScore", {}).get("direction") == "declined":
        output.append("Lateral stability score decreased compared with the previous stored session.")
    return output[:3]


def _repeated_patterns(current_trip: dict[str, Any], history_trips: list[dict[str, Any]]) -> list[str]:
    sessions = [current_trip, *history_trips]
    repeated: list[str] = []
    for pattern in PATTERNS:
        count = sum(1 for trip in sessions if _has_pattern(trip, pattern["eventTypes"]))
        if count >= 2:
            repeated.append(pattern["label"])
    return repeated[:3]


def _watch_items(current_trip: dict[str, Any], repeated_patterns: list[str], declines: list[str]) -> list[str]:
    current_event_types = _event_types(current_trip)
    items: list[str] = []
    for pattern in PATTERNS:
        if pattern["label"] in repeated_patterns or current_event_types.intersection(pattern["eventTypes"]):
            items.append(pattern["watchItem"])
    if declines and "Use the next drive to check whether the declined metric returns toward the previous baseline." not in items:
        items.append("Use the next drive to check whether the declined metric returns toward the previous baseline.")
    if not items:
        items.append("Maintain the current smooth control pattern and use the next session as another comparison point.")
    return items[:3]


def _behaviour_change_summary(score_trend: list[dict[str, Any]]) -> str:
    if len(score_trend) < 2:
        return "There is not enough stored history yet to describe a driving-behaviour trend."

    first = score_trend[0]
    last = score_trend[-1]
    first_score = float(first.get("overallScore") or 0)
    last_score = float(last.get("overallScore") or 0)
    score_delta = last_score - first_score
    first_events = int(first.get("riskEventCount") or 0)
    last_events = int(last.get("riskEventCount") or 0)
    event_delta = last_events - first_events

    if score_delta > 1 and event_delta <= 0:
        return "Across recent stored sessions, the overall score is trending upward while risk-event count is stable or lower."
    if score_delta < -1 or event_delta > 0:
        return "Across recent stored sessions, the latest drive needs more attention because score or risk-event count moved in the wrong direction."
    return "Across recent stored sessions, the driving pattern is broadly stable with no strong score movement yet."


def generate_memory_aware_coaching(trip: dict[str, Any], include_recent_sessions: int = 5) -> dict[str, Any]:
    current_id = str(trip.get("id"))
    limit = max(2, min(include_recent_sessions, 8))
    previous = previous_session(current_id)
    historical_trips = recent_session_trips(limit=limit - 1, exclude_id=current_id)
    comparison = compare_sessions(trip, previous)
    score_trend = _score_trend(trip, limit)
    improvements = _improvements(comparison)
    declines = _declines(comparison)
    repeated = _repeated_patterns(trip, historical_trips)
    watch_items = _watch_items(trip, repeated, declines)

    if previous is None:
        memory_summary = "This session is stored as the baseline for future coaching comparison."
    else:
        memory_summary = comparison.get("insights", ["This session is broadly similar to the previous stored session."])[0]

    if not repeated:
        repeated = ["No repeated pattern is established yet; keep collecting comparable route reviews."]

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sessionId": trip.get("id"),
        "agentMode": "deterministic_memory_aware_coaching",
        "hasMemory": previous is not None,
        "previousSessionId": previous.get("id") if previous else None,
        "memorySummary": memory_summary,
        "behaviourChangeSummary": _behaviour_change_summary(score_trend),
        "improvements": improvements or ["No clear improvement signal is established from the previous stored session yet."],
        "repeatedPatterns": repeated,
        "watchItems": watch_items,
        "scoreTrend": score_trend,
        "recentSessions": recent_sessions(limit=limit),
        "evidence": [
            f"Current session: {trip.get('id')}",
            f"Previous session: {previous.get('id') if previous else 'none'}",
            f"Current score: {_metric(trip, 'overallDrivingScore'):.1f}/100",
            f"Current risk events: {int(_metric(trip, 'riskEventCount'))}",
        ],
        "memoryPolicy": (
            "DriveCoach uses recent session memory only to compare measurable driving patterns. "
            "It does not create a driver diagnosis, medical inference, or long-term behavioural label."
        ),
    }
