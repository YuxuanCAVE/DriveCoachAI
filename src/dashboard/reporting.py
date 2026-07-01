from __future__ import annotations


def _event_counts(events: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        event_type = str(event["type"])
        counts[event_type] = counts.get(event_type, 0) + 1
    return counts


def build_coaching_report(
    behaviour_metrics: dict[str, float],
    physiological_metrics: dict[str, object],
    events: list[dict[str, object]],
) -> dict[str, list[str]]:
    """Create a deterministic coaching report draft without LLM generation."""
    counts = _event_counts(events)
    high_events = [event for event in events if event.get("severity") == "high"]
    lateral_score = behaviour_metrics["lateral_stability_score"]
    longitudinal_score = behaviour_metrics["longitudinal_smoothness_score"]
    hr_delta = float(physiological_metrics["hr_delta_percent"])
    baseline_hr = float(physiological_metrics["baseline_hr"])

    key_findings = [
        f"{len(events)} rule-based events detected; {len(high_events)} marked high severity.",
        f"Mean speed was {behaviour_metrics['mean_speed']:.1f} m/s with peak speed {behaviour_metrics['max_speed']:.1f} m/s.",
        f"Baseline heart rate was {baseline_hr:.1f} bpm; session mean changed by {hr_delta:+.1f}%.",
    ]

    behaviour_interpretation = [
        f"Lateral stability score is {lateral_score:.0f}/100 and longitudinal smoothness is {longitudinal_score:.0f}/100.",
        "Acceleration and yaw markers highlight the specific time windows that drove the risk-event count.",
    ]
    if counts.get("harsh_braking"):
        behaviour_interpretation.append("Harsh braking events suggest moments of late speed control or abrupt hazard response.")
    if counts.get("high_lateral_acceleration") or counts.get("sharp_yaw_motion"):
        behaviour_interpretation.append("Lateral acceleration or yaw events indicate cornering or steering transients worth reviewing.")

    driver_state = [
        "Heart-rate features are interpreted only as physiological activation indicators, not medical measures.",
        "Overlaying activation events with vehicle events helps identify time windows where driving demand and driver state changed together.",
    ]
    if hr_delta > 8:
        driver_state.append("The session shows a sustained elevation from baseline that may justify closer review of high-demand segments.")
    else:
        driver_state.append("Mean heart rate stayed close to baseline, with activation changes concentrated around flagged windows.")

    suggestions = [
        "Review the highest severity events first and compare speed, acceleration, yaw rate, and heart rate around each window.",
        "Use smoother brake and throttle transitions in repeated manoeuvres where longitudinal smoothness is reduced.",
        "Track whether physiological activation repeatedly rises before, during, or after specific road or automation contexts.",
    ]

    next_focus = [
        "Add road type and automation status labels to separate manual, assisted, urban, and high-speed segments.",
        "Compare this session with the next drive using the same event thresholds before adding LLM-generated narrative.",
    ]

    return {
        "Key findings": key_findings,
        "Behaviour interpretation": behaviour_interpretation,
        "Driver state interpretation": driver_state,
        "Coaching suggestions": suggestions,
        "Next session focus": next_focus,
    }
