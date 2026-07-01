from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.services.session_memory_service import previous_session


SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3}


def _round(value: Any, digits: int = 1) -> float:
    try:
        return round(float(value), digits)
    except (TypeError, ValueError):
        return 0.0


def _event_count(trip: dict[str, Any], event_types: set[str]) -> int:
    return len([event for event in trip.get("events", []) if event.get("type") in event_types])


def _event_segments(trip: dict[str, Any], event_types: set[str]) -> list[str]:
    segments: list[str] = []
    for event in trip.get("events", []):
        if event.get("type") in event_types:
            segment = event.get("segmentName")
            if segment and segment not in segments:
                segments.append(str(segment))
    return segments[:2]


def _highest_severity(trip: dict[str, Any], event_types: set[str]) -> str | None:
    severities = [
        str(event.get("severity", "low"))
        for event in trip.get("events", [])
        if event.get("type") in event_types
    ]
    if not severities:
        return None
    return sorted(severities, key=lambda severity: SEVERITY_RANK.get(severity, 1), reverse=True)[0]


def _previous_metric(previous: dict[str, Any] | None, key: str) -> float | None:
    if previous is None:
        return None
    value = previous.get("metrics", {}).get(key)
    return float(value) if isinstance(value, int | float) else None


def _previous_event_count(previous: dict[str, Any] | None, event_types: set[str]) -> int | None:
    if previous is None:
        return None
    return _event_count(previous, event_types)


def _trend(current: float, previous: float | None, lower_is_better: bool) -> str | None:
    if previous is None:
        return None
    delta = current - previous
    if abs(delta) < 0.05:
        return "unchanged"
    improved = delta < 0 if lower_is_better else delta > 0
    return "improved" if improved else "needs_attention"


def _target(
    *,
    target_id: str,
    title: str,
    category: str,
    priority: str,
    baseline_value: float,
    target_value: float,
    unit: str,
    measurement: str,
    why_it_matters: str,
    next_action: str,
    evidence: list[str],
    route_context: list[str],
    previous_value: float | None = None,
    lower_is_better: bool = True,
) -> dict[str, Any]:
    return {
        "id": target_id,
        "title": title,
        "category": category,
        "priority": priority,
        "baselineValue": baseline_value,
        "targetValue": target_value,
        "unit": unit,
        "measurement": measurement,
        "whyItMatters": why_it_matters,
        "nextAction": next_action,
        "evidence": evidence,
        "routeContext": route_context,
        "previousValue": previous_value,
        "trendVsPrevious": _trend(baseline_value, previous_value, lower_is_better) if previous_value is not None else None,
        "status": "active",
    }


def generate_coaching_targets(trip: dict[str, Any], include_history: bool = True) -> dict[str, Any]:
    metrics = trip.get("metrics", {})
    route = trip.get("route", {})
    events = trip.get("events", [])
    previous = previous_session(str(trip.get("id"))) if include_history else None

    braking_types = {"late_braking_before_curve", "harsh_braking"}
    lateral_types = {"high_lateral_acceleration", "unstable_cornering", "high_speed_in_curve", "sharp_yaw_motion"}
    speed_types = {"unstable_speed_control", "harsh_acceleration"}

    braking_count = _event_count(trip, braking_types)
    lateral_count = _event_count(trip, lateral_types)
    speed_count = _event_count(trip, speed_types)
    risk_count = int(metrics.get("riskEventCount", len(events)))

    targets: list[dict[str, Any]] = []

    if braking_count > 0 or _round(metrics.get("maxAbsAx")) >= 3.0:
        targets.append(
            _target(
                target_id="reduce-late-braking",
                title="Reduce late or harsh braking",
                category="behaviour",
                priority="high" if _highest_severity(trip, braking_types) == "high" else "medium",
                baseline_value=float(braking_count),
                target_value=float(max(0, braking_count - 1)),
                unit="events",
                measurement="Count of late_braking_before_curve and harsh_braking events; review peak longitudinal deceleration.",
                why_it_matters="Earlier, more progressive braking improves comfort and makes vehicle motion more predictable before higher-demand road sections.",
                next_action="Start speed reduction earlier before rural bends, village approaches, or junctions instead of correcting late.",
                evidence=[
                    f"{braking_count} braking-related event(s)",
                    f"Peak longitudinal acceleration: {_round(metrics.get('maxAbsAx'))} m/s^2",
                ],
                route_context=_event_segments(trip, braking_types) or [route.get("name", "Reviewed route")],
                previous_value=(
                    float(_previous_event_count(previous, braking_types))
                    if _previous_event_count(previous, braking_types) is not None
                    else None
                ),
            )
        )

    if lateral_count > 0 or _round(metrics.get("maxAbsAy")) >= 2.0:
        targets.append(
            _target(
                target_id="lower-cornering-demand",
                title="Lower peak cornering demand",
                category="route_context",
                priority="high" if _highest_severity(trip, lateral_types) == "high" else "medium",
                baseline_value=_round(metrics.get("maxAbsAy")),
                target_value=max(1.8, _round(metrics.get("maxAbsAy")) - 0.3),
                unit="m/s^2",
                measurement="Maximum absolute lateral acceleration on curve, bend, and junction-context sections.",
                why_it_matters="Lower lateral demand supports smoother cornering, better stability, and more predictable steering response.",
                next_action="Settle speed before entering high-curvature sections, then hold a smoother steering arc through the bend.",
                evidence=[
                    f"{lateral_count} lateral or curve-related event(s)",
                    f"Lateral stability score: {round(float(metrics.get('lateralStabilityScore', 0)))}/100",
                ],
                route_context=_event_segments(trip, lateral_types) or ["Country-road curve and junction context"],
                previous_value=_previous_metric(previous, "maxAbsAy"),
            )
        )

    if speed_count > 0 or _round(metrics.get("speedStd")) >= 3.0:
        targets.append(
            _target(
                target_id="stabilise-speed-control",
                title="Stabilise speed control",
                category="behaviour",
                priority="medium",
                baseline_value=_round(metrics.get("speedStd")),
                target_value=max(1.5, _round(metrics.get("speedStd")) - 0.4),
                unit="m/s std",
                measurement="Speed standard deviation, plus unstable_speed_control and harsh_acceleration event count.",
                why_it_matters="A steadier speed profile improves comfort and helps separate normal urban stop-go behaviour from avoidable pedal fluctuation.",
                next_action="Use smoother throttle and brake transitions during urban arrival and junction approaches.",
                evidence=[
                    f"{speed_count} speed-control event(s)",
                    f"Speed standard deviation: {_round(metrics.get('speedStd'))} m/s",
                ],
                route_context=_event_segments(trip, speed_types) or ["Urban arrival and junction approach"],
                previous_value=_previous_metric(previous, "speedStd"),
            )
        )

    if len(targets) < 3:
        current_score = _round(metrics.get("overallDrivingScore", metrics.get("overallSmoothnessScore", 0)), 0)
        targets.append(
            _target(
                target_id="improve-overall-smoothness",
                title="Improve overall smoothness score",
                category="measurable_score",
                priority="low" if risk_count <= 1 else "medium",
                baseline_value=current_score,
                target_value=min(100.0, current_score + 5),
                unit="score",
                measurement="Overall driving score from deterministic telemetry metrics and risk-event penalties.",
                why_it_matters="A score target keeps the next drive focused on measurable changes rather than a generic coaching suggestion.",
                next_action="Review the highest-priority target first, then compare the next session against this baseline.",
                evidence=[
                    f"Overall driving score: {round(float(metrics.get('overallDrivingScore', 0)))}/100",
                    f"Risk events: {risk_count}",
                ],
                route_context=[f"{route.get('origin', 'Origin')} to {route.get('destination', 'Destination')}"],
                previous_value=_previous_metric(previous, "overallDrivingScore"),
                lower_is_better=False,
            )
        )

    selected_targets = targets[:3]
    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sessionId": trip.get("id"),
        "agentMode": "deterministic_coaching_targets",
        "evidencePolicy": (
            "Targets are calculated from deterministic metrics and risk events. The AI coach can explain them, "
            "but the measurement criteria remain explicit."
        ),
        "hasHistory": previous is not None,
        "previousSessionId": previous.get("id") if previous else None,
        "targets": selected_targets,
    }
