from __future__ import annotations

from time import perf_counter
from typing import Any

from backend.agent.deepseek_client import DeepSeekReportError, generate_deepseek_report, is_deepseek_configured
from backend.agent.knowledge import retrieve_knowledge_snippets
from backend.agent.state import CoachAgentState
from backend.evaluation.report_evaluator import evaluate_coach_report
from backend.evaluation.trace_store import record_agent_trace


def _event_types(events: list[dict[str, Any]]) -> set[str]:
    return {str(event.get("type", "")) for event in events}


def _severity_weight(event: dict[str, Any]) -> int:
    severity = event.get("severity")
    if severity == "high":
        return 3
    if severity == "medium":
        return 2
    return 1


def _build_report_evidence(route: dict[str, Any], metrics: dict[str, Any], events: list[dict[str, Any]]) -> list[dict[str, str]]:
    evidence = [
        {
            "type": "metric",
            "label": "Overall driving score",
            "value": f"{round(float(metrics.get('overallDrivingScore', metrics.get('overallSmoothnessScore', 0))))}/100",
        },
        {
            "type": "metric",
            "label": "Context adaptation score",
            "value": f"{round(float(metrics.get('contextAdaptationScore', 0)))}/100",
        },
        {
            "type": "metric",
            "label": "Risk event count",
            "value": str(int(metrics.get("riskEventCount", len(events)))),
        },
        {
            "type": "route_segment",
            "label": "Reviewed route",
            "value": f"{route.get('origin', 'Origin')} to {route.get('destination', 'Destination')}",
        },
    ]

    for event in events[:3]:
        evidence.append(
            {
                "type": "event",
                "label": str(event.get("type", "risk_event")).replace("_", " ").title(),
                "value": f"{event.get('segmentName', 'route segment')} · {event.get('severity', 'medium')} severity",
            }
        )

    return evidence


def _workflow_node_names() -> list[str]:
    return [
        "LoadTripNode",
        "AnalyseEvidenceNode",
        "RetrieveKnowledgeNode",
        "GenerateCoachReportNode",
        "ValidateReportNode",
        "ReviseReportNode",
    ]


def _default_summary(route: dict[str, Any], metrics: dict[str, Any], events: list[dict[str, Any]]) -> str:
    route_name = route.get("name", "the completed route")
    score = round(float(metrics.get("overallDrivingScore", metrics.get("overallSmoothnessScore", 0))))
    event_count = int(metrics.get("riskEventCount", len(events)))
    return (
        f"{route_name} shows a {score}/100 driving profile with {event_count} deterministic risk events; "
        "the coaching focus should stay grounded in route context and vehicle telemetry."
    )


def _fallback_key_findings(route: dict[str, Any], metrics: dict[str, Any], events: list[dict[str, Any]]) -> list[str]:
    origin = route.get("origin", "Origin")
    destination = route.get("destination", "Destination")
    return [
        f"Driving score: {round(float(metrics.get('overallDrivingScore', metrics.get('overallSmoothnessScore', 0))))}/100.",
        f"{int(metrics.get('riskEventCount', len(events)))} deterministic risk events were detected from vehicle telemetry.",
        f"The reviewed route runs from {origin} to {destination}.",
    ]


def _sanitize_report_text(value: Any) -> Any:
    replacements = {
        "stress detected": "optional driver-state activation context",
        "fatigue detected": "optional driver-state activation context",
        "diagnosis": "interpretation",
        "diagnose": "interpret",
        "medical condition": "driver-state context",
        "health risk": "unsupported health interpretation",
    }
    if isinstance(value, str):
        sanitized = value
        for source, target in replacements.items():
            sanitized = sanitized.replace(source, target).replace(source.capitalize(), target).replace(source.title(), target)
        return sanitized
    if isinstance(value, list):
        return [_sanitize_report_text(item) for item in value]
    if isinstance(value, dict):
        return {key: _sanitize_report_text(item) for key, item in value.items()}
    return value


def load_session_node(state: CoachAgentState) -> CoachAgentState:
    trip = state["trip"]
    return {
        **state,
        "route_context": trip.get("route", {}),
        "metrics": trip.get("metrics", {}),
        "events": trip.get("events", []),
        "mode": state.get("mode", "deterministic_agent_no_llm"),
    }


def analyse_evidence_node(state: CoachAgentState) -> CoachAgentState:
    events = state.get("events", [])
    metrics = state.get("metrics", {})
    event_types = _event_types(events)
    severity_counts = {
        "low": sum(1 for event in events if event.get("severity") == "low"),
        "medium": sum(1 for event in events if event.get("severity") == "medium"),
        "high": sum(1 for event in events if event.get("severity") == "high"),
    }
    highest_priority_event = sorted(events, key=_severity_weight, reverse=True)[0] if events else None
    evidence_summary = {
        "eventTypes": sorted(event_types),
        "severityCounts": severity_counts,
        "highestPriorityEvent": highest_priority_event,
        "riskEventCount": int(metrics.get("riskEventCount", len(events))),
        "overallDrivingScore": metrics.get("overallDrivingScore", metrics.get("overallSmoothnessScore")),
        "contextAdaptationScore": metrics.get("contextAdaptationScore"),
        "wearableConnected": bool(metrics.get("wearableConnected", False)),
    }

    return {**state, "evidence_summary": evidence_summary}


def retrieve_knowledge_node(state: CoachAgentState) -> CoachAgentState:
    events = state.get("events", [])
    event_types = set(state.get("evidence_summary", {}).get("eventTypes", [])) or _event_types(events)
    retrieved_knowledge = retrieve_knowledge_snippets(
        events,
        route_context=state.get("route_context", {}),
        metrics=state.get("metrics", {}),
        limit=6,
    )
    guidance = [
        "Use deterministic vehicle metrics as evidence before generating coaching language.",
        "Separate route context from driver-state context; wearable data is optional.",
        "Avoid medical, fatigue, or stress diagnosis from heart-rate features.",
    ]

    if "late_braking_before_curve" in event_types or "harsh_braking" in event_types:
        guidance.append("For braking events, focus on earlier speed reduction and more progressive brake input.")
    if "high_lateral_acceleration" in event_types or "unstable_cornering" in event_types:
        guidance.append("For cornering events, focus on lower entry speed and smoother steering demand.")
    if "sharp_yaw_motion" in event_types:
        guidance.append("For yaw events, focus on avoiding abrupt steering corrections.")
    if "unstable_speed_control" in event_types:
        guidance.append("For unstable speed control, focus on steadier following speed and smoother throttle transitions.")

    guidance.extend(snippet["body"] for snippet in retrieved_knowledge)

    return {**state, "guidance_context": guidance, "retrieved_knowledge": retrieved_knowledge}


def generate_report_node(state: CoachAgentState) -> CoachAgentState:
    trip = state["trip"]
    route = state.get("route_context", {})
    metrics = state.get("metrics", {})
    events = state.get("events", [])
    event_types = _event_types(events)

    route_name = route.get("name", "the completed route")
    origin = route.get("origin", "the origin")
    destination = route.get("destination", "the destination")
    score = round(float(metrics.get("overallDrivingScore", metrics.get("overallSmoothnessScore", 0))))
    context_score = round(float(metrics.get("contextAdaptationScore", 0)))
    event_count = int(metrics.get("riskEventCount", len(events)))

    has_braking = "late_braking_before_curve" in event_types or "harsh_braking" in event_types
    has_lateral = "high_lateral_acceleration" in event_types or "unstable_cornering" in event_types
    has_speed_curve = "high_speed_in_curve" in event_types
    has_speed_instability = "unstable_speed_control" in event_types

    if score >= 82 and event_count <= 2:
        summary = (
            f"{route_name} was mostly smooth, with the strongest evidence showing controlled vehicle motion "
            "and limited risk events."
        )
    else:
        summary = (
            f"{route_name} shows useful coaching opportunities around route context, especially where speed "
            "choice, braking timing, or lateral demand increased."
        )

    main_behavioural_pattern = "Vehicle control was generally smooth, with no dominant risk pattern detected."
    if has_braking and has_lateral:
        main_behavioural_pattern = (
            "The main pattern is late speed reduction before demanding route sections, followed by higher lateral demand."
        )
    elif has_braking:
        main_behavioural_pattern = "The main pattern is late or firmer braking before a higher-demand segment."
    elif has_lateral:
        main_behavioural_pattern = "The main pattern is elevated cornering demand, linked to entry speed and steering smoothness."
    elif has_speed_instability:
        main_behavioural_pattern = "The main pattern is unstable speed control during lower-speed urban arrival."

    route_context_explanation = (
        f"The evidence is route-aware: this review follows {origin} to {destination}, including campus departure, "
        "rural roads, bends, junction context, and urban arrival. The coaching priority comes from where the events "
        "occurred, not only from the overall score."
    )

    why_it_matters = (
        "This matters because smoother speed choice, braking, and steering inputs improve comfort, vehicle stability, "
        "and predictability for the next similar route context. The report does not infer medical state or driver fatigue."
    )

    key_findings = [
        f"Driving score: {score}/100; context adaptation score: {context_score}/100.",
        f"{event_count} deterministic risk events were detected from vehicle telemetry.",
        f"The reviewed route runs from {origin} to {destination}.",
    ]

    if events:
        most_important_event = sorted(events, key=_severity_weight, reverse=True)[0]
        key_findings.append(
            "Highest-priority event: "
            f"{str(most_important_event.get('type', '')).replace('_', ' ')} "
            f"in {most_important_event.get('segmentName', 'the route segment')}."
        )

    if has_speed_curve:
        key_findings.append("Speed stayed above the route target during at least one higher-curvature segment.")

    behaviour_parts = [
        "The analysis links each event to route context rather than treating the session as one generic drive."
    ]
    if has_braking:
        behaviour_parts.append("The braking evidence suggests a need to reduce speed earlier before demanding segments.")
    if has_lateral:
        behaviour_parts.append("The lateral-motion evidence points to corner entry speed and steering smoothness as key factors.")
    if has_speed_instability:
        behaviour_parts.append("The urban-arrival evidence shows speed variation that should be reviewed separately from open-road cruising.")
    if not events:
        behaviour_parts.append("No risk events were detected, so this scenario is useful as a smooth baseline.")

    wearable_connected = bool(metrics.get("wearableConnected", False))
    if wearable_connected:
        driver_state_insight = (
            "Optional wearable context was connected. Heart-rate values are used only as driver-state context "
            "alongside telemetry evidence, not as a medical or fatigue assessment."
        )
    else:
        driver_state_insight = (
            "Wearable data is not connected. This coaching report is based on connected-vehicle telemetry only."
        )

    next_focus = []
    if has_braking:
        next_focus.append("Brake earlier and more progressively before similar rural curves or junction approaches.")
    if has_lateral:
        next_focus.append("Use a lower, steadier entry speed before high-curvature road sections.")
    if has_speed_instability:
        next_focus.append("Keep throttle and braking transitions smoother during urban arrival and stop-go traffic.")
    if not next_focus:
        next_focus.append("Maintain the current smooth control pattern and use this trip as a reference baseline.")
    next_focus.append("Review route segments separately: campus exit, rural roads, bends, junctions, and urban arrival.")

    event_suggestions = [
        {
            "eventId": event.get("id"),
            "type": event.get("type"),
            "segmentName": event.get("segmentName"),
            "severity": event.get("severity"),
            "suggestion": event.get("coachingSuggestion"),
        }
        for event in events[:4]
    ]
    evidence_used = _build_report_evidence(route, metrics, events)
    retrieved_knowledge = state.get("retrieved_knowledge", [])
    retrieved_knowledge_summary = [
        {
            "id": snippet.get("id"),
            "title": snippet.get("title"),
            "source": snippet.get("source"),
            "confidence": snippet.get("confidence"),
            "matchedBy": snippet.get("matchedBy", []),
            "whyUsed": snippet.get("whyUsed"),
            "retrievalMode": snippet.get("retrievalMode"),
        }
        for snippet in retrieved_knowledge
    ]

    fallback_report = {
        "summary": summary,
        "structuredSummary": {
            "overallAssessment": summary,
            "mainBehaviouralPattern": main_behavioural_pattern,
            "routeContextExplanation": route_context_explanation,
            "whyItMatters": why_it_matters,
            "nextDriveFocus": next_focus[:3],
        },
        "keyFindings": key_findings,
        "behaviourInsight": " ".join(behaviour_parts),
        "driverStateInsight": driver_state_insight,
        "nextSessionFocus": next_focus,
        "eventSuggestions": event_suggestions,
        "evidenceUsed": evidence_used,
        "retrievedKnowledge": retrieved_knowledge_summary,
        "agentMode": state.get("mode", "deterministic_agent_no_llm"),
        "workflowEngine": state.get("workflow_engine", "python_node_runner"),
        "workflowNodes": state.get(
            "workflow_nodes",
            _workflow_node_names(),
        ),
        "evidencePolicy": (
            "Metrics and risk events are calculated deterministically. The AI coach explains the evidence "
            "and turns it into practical guidance."
        ),
        "sessionId": trip.get("id"),
    }

    if is_deepseek_configured():
        try:
            report = generate_deepseek_report(state, fallback_report)
        except DeepSeekReportError as error:
            report = {
                **fallback_report,
                "agentMode": "deepseek_failed_deterministic_fallback",
                "llmFallbackReason": str(error),
            }
        except Exception as error:  # pragma: no cover - protects runtime API calls
            report = {
                **fallback_report,
                "agentMode": "deepseek_failed_deterministic_fallback",
                "llmFallbackReason": error.__class__.__name__,
            }
    else:
        report = fallback_report

    return {**state, "report": report}


def validate_report_node(state: CoachAgentState) -> CoachAgentState:
    report = state.get("report", {})
    notes: list[str] = []
    required_fields = ["summary", "keyFindings", "behaviourInsight", "nextSessionFocus"]

    for field in required_fields:
        if not report.get(field):
            notes.append(f"Missing report field: {field}")

    report_text = str(report).lower()
    allowed_medical_context = any(
        phrase in report_text
        for phrase in [
            "not as a medical",
            "not infer medical",
            "without making medical",
            "not a medical",
        ]
    )
    if "medical" in report_text and not allowed_medical_context:
        notes.append("Report may contain unsupported medical language.")

    passed = not notes
    if passed:
        notes.append("Report passed deterministic evidence and schema checks.")

    report_validation = {
        "passed": passed,
        "notes": notes,
        "revisionCount": int(state.get("revision_count", 0)),
    }
    report = {
        **report,
        "validationNotes": notes,
        "reportValidation": report_validation,
        "revisionCount": int(state.get("revision_count", 0)),
        "revisionApplied": int(state.get("revision_count", 0)) > 0,
    }
    return {**state, "report": report, "validation_notes": notes, "report_validation": report_validation}


def revise_report_node(state: CoachAgentState) -> CoachAgentState:
    report = _sanitize_report_text(state.get("report", {}))
    route = state.get("route_context", {})
    metrics = state.get("metrics", {})
    events = state.get("events", [])
    revision_count = int(state.get("revision_count", 0)) + 1

    summary = report.get("summary") or _default_summary(route, metrics, events)
    structured_summary = report.get("structuredSummary") if isinstance(report.get("structuredSummary"), dict) else {}
    next_focus = report.get("nextSessionFocus") if isinstance(report.get("nextSessionFocus"), list) else []
    if not next_focus:
        next_focus = [
            "Review the highest-demand route segment first.",
            "Use smoother braking, throttle, and steering transitions in the next comparable drive.",
        ]

    structured_summary = {
        "overallAssessment": structured_summary.get("overallAssessment") or summary,
        "mainBehaviouralPattern": structured_summary.get("mainBehaviouralPattern")
        or report.get("behaviourInsight")
        or "The dominant pattern should be interpreted from deterministic vehicle telemetry and route context.",
        "routeContextExplanation": structured_summary.get("routeContextExplanation")
        or f"The reviewed route runs from {route.get('origin', 'Origin')} to {route.get('destination', 'Destination')}.",
        "whyItMatters": structured_summary.get("whyItMatters")
        or "This matters for comfort, stability, and predictability without making medical or fatigue claims.",
        "nextDriveFocus": structured_summary.get("nextDriveFocus") or next_focus[:3],
    }

    revised_report = {
        **report,
        "summary": summary,
        "structuredSummary": structured_summary,
        "keyFindings": report.get("keyFindings") or _fallback_key_findings(route, metrics, events),
        "behaviourInsight": report.get("behaviourInsight")
        or "The report was revised to keep the explanation grounded in deterministic route and telemetry evidence.",
        "nextSessionFocus": next_focus,
        "evidenceUsed": report.get("evidenceUsed") or _build_report_evidence(route, metrics, events),
        "retrievedKnowledge": report.get("retrievedKnowledge")
        or [
            {
                "id": snippet.get("id"),
                "title": snippet.get("title"),
                "source": snippet.get("source"),
                "confidence": snippet.get("confidence"),
                "matchedBy": snippet.get("matchedBy", []),
                "whyUsed": snippet.get("whyUsed"),
                "retrievalMode": snippet.get("retrievalMode"),
            }
            for snippet in state.get("retrieved_knowledge", [])
        ],
        "revisionCount": revision_count,
        "revisionApplied": True,
        "revisionReason": "; ".join(state.get("validation_notes", [])),
    }

    return {**state, "report": revised_report, "revision_count": revision_count}


WORKFLOW_NODES = [
    load_session_node,
    analyse_evidence_node,
    retrieve_knowledge_node,
    generate_report_node,
    validate_report_node,
]


def should_revise_report(state: CoachAgentState) -> str:
    validation = state.get("report_validation", {})
    if validation.get("passed", False):
        return "return"
    if int(state.get("revision_count", 0)) >= 1:
        return "return"
    return "revise"


def run_python_node_workflow(trip: dict[str, Any]) -> dict[str, Any]:
    state: CoachAgentState = {
        "trip": trip,
        "workflow_engine": "python_node_runner",
        "workflow_nodes": _workflow_node_names(),
    }
    for node in WORKFLOW_NODES:
        state = node(state)
    if should_revise_report(state) == "revise":
        state = revise_report_node(state)
        state = validate_report_node(state)
    return state["report"]


def run_coach_workflow(trip: dict[str, Any]) -> dict[str, Any]:
    started_at = perf_counter()
    try:
        from backend.agent.langgraph_workflow import run_langgraph_coach_workflow

        report = run_langgraph_coach_workflow(trip)
    except Exception as error:  # pragma: no cover - protects runtime graph setup
        report = run_python_node_workflow(trip)
        report = {
            **report,
            "workflowEngine": "python_node_runner",
            "workflowFallbackReason": error.__class__.__name__,
        }

    duration_ms = round((perf_counter() - started_at) * 1000)
    evaluation = evaluate_coach_report(report, trip, duration_ms=duration_ms)
    report = {**report, "evaluation": evaluation}

    try:
        trace_metadata = record_agent_trace(report, trip, evaluation)
        report = {**report, "trace": trace_metadata}
    except Exception as error:  # pragma: no cover - observability must not break report generation
        report = {**report, "trace": {"recorded": False, "error": error.__class__.__name__}}

    return report
