from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.services.coaching_target_service import generate_coaching_targets
from backend.services.session_memory_service import previous_session


LOWER_IS_BETTER_TARGETS = {
    "reduce-late-braking",
    "lower-cornering-demand",
    "stabilise-speed-control",
}


def _event_count(trip: dict[str, Any], event_types: set[str]) -> int:
    return len([event for event in trip.get("events", []) if event.get("type") in event_types])


def _current_value_for_target(trip: dict[str, Any], target_id: str) -> float:
    metrics = trip.get("metrics", {})
    if target_id == "reduce-late-braking":
        return float(_event_count(trip, {"late_braking_before_curve", "harsh_braking"}))
    if target_id == "lower-cornering-demand":
        return float(metrics.get("maxAbsAy", 0))
    if target_id == "stabilise-speed-control":
        return float(metrics.get("speedStd", 0))
    if target_id == "improve-overall-smoothness":
        return float(metrics.get("overallDrivingScore", metrics.get("overallSmoothnessScore", 0)))
    return float(metrics.get("overallDrivingScore", 0))


def _is_completed(target: dict[str, Any], current_value: float) -> bool:
    target_value = float(target.get("targetValue", 0))
    if target.get("id") in LOWER_IS_BETTER_TARGETS:
        return current_value <= target_value
    return current_value >= target_value


def _progress_delta(target: dict[str, Any], current_value: float) -> float:
    baseline = float(target.get("baselineValue", 0))
    if target.get("id") in LOWER_IS_BETTER_TARGETS:
        return baseline - current_value
    return current_value - baseline


def _target_result(target: dict[str, Any], current_trip: dict[str, Any]) -> dict[str, Any]:
    current_value = _current_value_for_target(current_trip, str(target.get("id")))
    completed = _is_completed(target, current_value)
    delta = _progress_delta(target, current_value)
    return {
        "targetId": target.get("id"),
        "title": target.get("title"),
        "category": target.get("category"),
        "priority": target.get("priority"),
        "unit": target.get("unit"),
        "previousBaselineValue": target.get("baselineValue"),
        "targetValue": target.get("targetValue"),
        "currentValue": round(current_value, 2),
        "progressDelta": round(delta, 2),
        "completed": completed,
        "status": "completed" if completed else "continue_focus",
        "measurement": target.get("measurement"),
        "nextAction": (
            "Target achieved. Move to the next measurable coaching focus."
            if completed
            else target.get("nextAction", "Continue this target in the next drive.")
        ),
        "evidence": target.get("evidence", []),
        "routeContext": target.get("routeContext", []),
    }


def _deduplicate_targets(targets: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    output: list[dict[str, Any]] = []
    for target in targets:
        target_id = str(target.get("id"))
        if target_id in seen:
            continue
        seen.add(target_id)
        output.append(target)
    return output


def evaluate_target_completion(current_trip: dict[str, Any]) -> dict[str, Any]:
    previous = previous_session(str(current_trip.get("id")))
    current_targets_response = generate_coaching_targets(current_trip, include_history=True)
    current_targets = current_targets_response.get("targets", [])

    if previous is None:
        return {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "sessionId": current_trip.get("id"),
            "agentMode": "deterministic_target_completion",
            "hasPreviousTargets": False,
            "previousSessionId": None,
            "summary": "No previous coaching targets are available yet. This session creates the baseline target set.",
            "completionRate": 0,
            "completedCount": 0,
            "totalPreviousTargets": 0,
            "results": [],
            "completedTargets": [],
            "continuingFocus": [],
            "newlyGeneratedTargets": current_targets[:3],
            "activeTargets": current_targets[:3],
            "policy": "Target completion is calculated deterministically from previous target measurements and current telemetry metrics.",
        }

    previous_targets_response = generate_coaching_targets(previous, include_history=False)
    previous_targets = previous_targets_response.get("targets", [])
    results = [_target_result(target, current_trip) for target in previous_targets]
    completed_targets = [result for result in results if result["completed"]]
    continuing_focus_results = [result for result in results if not result["completed"]]

    continuing_focus_targets: list[dict[str, Any]] = []
    for result in continuing_focus_results:
        previous_target = next(target for target in previous_targets if target.get("id") == result["targetId"])
        continuing_focus_targets.append(
            {
                **previous_target,
                "status": "continue_focus",
                "previousBaselineValue": result["previousBaselineValue"],
                "currentValue": result["currentValue"],
                "targetValue": result["targetValue"],
            }
        )

    new_target_ids = {target.get("id") for target in current_targets}
    newly_generated_targets = [
        {**target, "status": "new_after_completion" if completed_targets else "active"}
        for target in current_targets
        if target.get("id") not in {result["targetId"] for result in continuing_focus_results}
        or target.get("id") not in new_target_ids
    ]
    active_targets = _deduplicate_targets([*continuing_focus_targets, *newly_generated_targets])[:3]

    completed_count = len(completed_targets)
    total = len(results)
    completion_rate = round((completed_count / total) * 100) if total else 0
    if total and completed_count == total:
        summary = "All previous coaching targets were achieved. DriveCoach generated a fresh target set for the next session."
    elif completed_count:
        summary = f"{completed_count} of {total} previous targets were achieved. Unfinished targets remain in focus, with new targets added where useful."
    else:
        summary = "Previous targets were not completed yet. DriveCoach will keep the same focus before introducing a harder goal."

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sessionId": current_trip.get("id"),
        "agentMode": "deterministic_target_completion",
        "hasPreviousTargets": True,
        "previousSessionId": previous.get("id"),
        "summary": summary,
        "completionRate": completion_rate,
        "completedCount": completed_count,
        "totalPreviousTargets": total,
        "results": results,
        "completedTargets": completed_targets,
        "continuingFocus": continuing_focus_targets,
        "newlyGeneratedTargets": newly_generated_targets[:3],
        "activeTargets": active_targets,
        "policy": "Target completion is calculated deterministically from previous target measurements and current telemetry metrics.",
    }
