from __future__ import annotations

from typing import Any

from backend.agent.deepseek_client import DeepSeekReportError, generate_deepseek_chat_response, is_deepseek_configured
from backend.agent.knowledge import retrieve_knowledge_snippets
from backend.services.memory_aware_coaching_service import generate_memory_aware_coaching


def _latest_user_question(messages: list[dict[str, str]]) -> str:
    for message in reversed(messages):
        if message.get("role") == "user":
            return message.get("content", "")
    return "What should I focus on next?"


def _primary_event(trip: dict[str, Any], selected_event: dict[str, Any] | None) -> dict[str, Any] | None:
    if selected_event:
        return selected_event
    events = trip.get("events", [])
    return events[0] if events else None


def _format_event_type(event_type: str | None) -> str:
    return (event_type or "driving event").replace("_", " ")


def _build_evidence_used(
    trip: dict[str, Any],
    selected_event: dict[str, Any] | None,
    snippets: list[dict[str, Any]],
) -> list[dict[str, str]]:
    metrics = trip.get("metrics", {})
    route = trip.get("route", {})
    event = _primary_event(trip, selected_event)
    evidence = [
        {
            "type": "metric",
            "label": "Driving score",
            "value": f"{round(float(metrics.get('overallDrivingScore', 0)))}/100",
        },
        {
            "type": "route_segment",
            "label": "Reviewed route",
            "value": f"{route.get('origin', 'Origin')} to {route.get('destination', 'Destination')}",
        },
    ]

    if event:
        evidence.append(
            {
                "type": "event",
                "label": _format_event_type(str(event.get("type", ""))).title(),
                "value": f"{event.get('segmentName', 'route segment')} · {event.get('severity', 'medium')} severity",
            }
        )

    evidence.extend(
        {"type": "knowledge", "label": snippet["title"], "value": snippet["id"]}
        for snippet in snippets[:3]
    )
    return evidence


def _deterministic_chat_response(
    trip: dict[str, Any],
    messages: list[dict[str, str]],
    selected_event: dict[str, Any] | None,
    snippets: list[dict[str, Any]],
) -> dict[str, Any]:
    question = _latest_user_question(messages).lower()
    metrics = trip.get("metrics", {})
    event = _primary_event(trip, selected_event)
    event_type = str(event.get("type", "")) if event else ""
    event_name = _format_event_type(event_type)
    segment = event.get("segmentName", "the route") if event else "the route"
    memory_context: dict[str, Any] | None = None
    asks_about_memory = any(
        phrase in question
        for phrase in ["last drive", "previous", "history", "trend", "repeated", "pattern", "improve from"]
    )

    if asks_about_memory:
        memory_context = generate_memory_aware_coaching(trip, include_recent_sessions=5)
        answer = (
            f"{memory_context['memorySummary']} {memory_context['behaviourChangeSummary']} "
            "I would treat this as a measurable session comparison, not a long-term driver label."
        )
        actions = memory_context["watchItems"][:3]
    elif "heart" in question or "wearable" in question:
        if metrics.get("wearableConnected"):
            answer = (
                "Wearable data is connected, so I can use heart-rate values as optional driver-state context. "
                f"For this session, mean heart rate was about {metrics.get('meanHeartRate', 0):.0f} bpm. "
                "I would not treat that as a medical or stress conclusion; it is only supporting context next to vehicle telemetry."
            )
            actions = [
                "Review whether heart-rate changes happened near detected driving events.",
                "Keep the main coaching focus on vehicle control evidence.",
            ]
        else:
            answer = (
                "Wearable data is not connected for this session. The coaching answer is therefore based on vehicle telemetry, "
                "route context, and detected risk events only."
            )
            actions = ["Use vehicle telemetry as the primary evidence source.", "Connect wearable data only if optional driver-state context is needed."]
    elif "why" in question or "risk" in question:
        if event:
            answer = (
                f"The main reason this matters is that {event_name} was detected in {segment}. "
                f"The event evidence indicates {event.get('shortExplanation', 'a higher-demand driving moment')}. "
                "In coaching terms, this is useful because it links the behaviour to a specific route context instead of giving a generic score."
            )
        else:
            answer = (
                "No risk event is selected. The session can be reviewed from the overall metrics and route context, "
                "but there is no specific event that needs explanation."
            )
        actions = [snippet["body"] for snippet in snippets if snippet["id"] not in {"policy_evidence_first", "policy_wearable_context"}][:2]
    elif "improve" in question or "next" in question or "focus" in question:
        answer = (
            "For the next drive, focus on one or two controllable behaviours rather than the whole score. "
            f"If this session is representative, the priority is {event_name} around {segment}."
        )
        actions = [
            "Reduce speed earlier before demanding route segments.",
            "Keep braking, throttle, and steering transitions progressive.",
            "Review similar route contexts separately from smooth cruising sections.",
        ]
    else:
        answer = (
            "This session is best interpreted as a route-aware review: the system combines deterministic metrics, "
            "risk events, and route segments, then turns those signals into coaching guidance."
        )
        if event:
            answer += f" The first event to inspect is {event_name} in {segment}."
        actions = [
            "Start with the highest-priority detected event.",
            "Compare the event segment with smoother parts of the same route.",
        ]

    return {
        "answer": answer,
        "evidenceUsed": _build_evidence_used(trip, selected_event, snippets)
        + (
            [
                {"type": "memory", "label": "Previous-drive comparison", "value": memory_context["previousSessionId"] or "baseline"},
                {"type": "memory", "label": "Score trend sessions", "value": str(len(memory_context["scoreTrend"]))},
            ]
            if memory_context
            else []
        ),
        "coachingActions": actions,
        "confidence": "high" if trip.get("events") else "medium",
        "safetyNotes": [
            "This answer is grounded in deterministic telemetry metrics and rule-based event detection.",
            "Wearable data, when available, is optional context only and not a medical assessment.",
        ],
        "followUpQuestions": [
            "Did I improve from last drive?",
            "Why was this event detected?",
            "What should I focus on next drive?",
            "Is this becoming a repeated pattern?",
        ],
        "agentMode": "deterministic_chat_no_llm",
        "retrievedKnowledge": [
            {
                "id": snippet["id"],
                "title": snippet["title"],
                "source": snippet.get("source"),
                "confidence": snippet.get("confidence"),
                "matchedBy": snippet.get("matchedBy", []),
                "whyUsed": snippet.get("whyUsed"),
                "retrievalMode": snippet.get("retrievalMode"),
            }
            for snippet in snippets
        ],
    }


def run_coach_chat(
    trip: dict[str, Any],
    messages: list[dict[str, str]],
    selected_event: dict[str, Any] | None = None,
) -> dict[str, Any]:
    events = trip.get("events", [])
    snippets = retrieve_knowledge_snippets(
        events,
        selected_event=selected_event,
        question=_latest_user_question(messages),
        route_context=trip.get("route", {}),
        metrics=trip.get("metrics", {}),
    )
    fallback_response = _deterministic_chat_response(trip, messages, selected_event, snippets)

    if is_deepseek_configured():
        try:
            return generate_deepseek_chat_response(trip, messages, selected_event, snippets, fallback_response)
        except DeepSeekReportError as error:
            return {
                **fallback_response,
                "agentMode": "deepseek_failed_deterministic_chat_fallback",
                "llmFallbackReason": str(error),
            }
        except Exception as error:  # pragma: no cover - protects runtime API calls
            return {
                **fallback_response,
                "agentMode": "deepseek_failed_deterministic_chat_fallback",
                "llmFallbackReason": error.__class__.__name__,
            }

    return fallback_response
