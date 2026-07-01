from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - exercised only when dependency is missing
    OpenAI = None  # type: ignore[assignment]


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_DEFAULT_MODEL = "deepseek-v4-flash"
PROJECT_ROOT = Path(__file__).resolve().parents[2]


class DeepSeekReportError(RuntimeError):
    pass


def _env_from_dotenv(name: str) -> str | None:
    dotenv_path = PROJECT_ROOT / ".env"
    if not dotenv_path.exists():
        return None

    for line in dotenv_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        if key.strip() == name:
            return value.strip().strip('"').strip("'")
    return None


def _get_env(name: str, default: str | None = None) -> str | None:
    return os.environ.get(name) or _env_from_dotenv(name) or default


def is_deepseek_configured() -> bool:
    return bool(_get_env("DEEPSEEK_API_KEY")) and OpenAI is not None


def _compact_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "type": event.get("type"),
            "severity": event.get("severity"),
            "segmentName": event.get("segmentName"),
            "startTime": event.get("startTime"),
            "endTime": event.get("endTime"),
            "evidence": event.get("evidence", {}),
            "shortExplanation": event.get("shortExplanation"),
            "coachingSuggestion": event.get("coachingSuggestion"),
        }
        for event in events[:8]
    ]


def _build_llm_payload(state: dict[str, Any], fallback_report: dict[str, Any]) -> dict[str, Any]:
    metrics = state.get("metrics", {})
    return {
        "route": state.get("route_context", {}),
        "metrics": {
            "overallDrivingScore": metrics.get("overallDrivingScore"),
            "overallSmoothnessScore": metrics.get("overallSmoothnessScore"),
            "longitudinalSmoothnessScore": metrics.get("longitudinalSmoothnessScore"),
            "lateralStabilityScore": metrics.get("lateralStabilityScore"),
            "contextAdaptationScore": metrics.get("contextAdaptationScore"),
            "riskEventCount": metrics.get("riskEventCount"),
            "wearableConnected": metrics.get("wearableConnected"),
            "meanHeartRate": metrics.get("meanHeartRate"),
            "maxHeartRate": metrics.get("maxHeartRate"),
            "baselineHeartRate": metrics.get("baselineHeartRate"),
            "heartRateDeltaPercent": metrics.get("heartRateDeltaPercent"),
        },
        "events": _compact_events(state.get("events", [])),
        "evidenceSummary": state.get("evidence_summary", {}),
        "guidanceContext": state.get("guidance_context", []),
        "retrievedKnowledge": state.get("retrieved_knowledge", []),
        "fallbackReport": {
            "summary": fallback_report.get("summary"),
            "structuredSummary": fallback_report.get("structuredSummary"),
            "keyFindings": fallback_report.get("keyFindings"),
            "behaviourInsight": fallback_report.get("behaviourInsight"),
            "driverStateInsight": fallback_report.get("driverStateInsight"),
            "nextSessionFocus": fallback_report.get("nextSessionFocus"),
            "evidenceUsed": fallback_report.get("evidenceUsed"),
            "retrievedKnowledge": fallback_report.get("retrievedKnowledge"),
        },
    }


def _extract_json(content: str) -> dict[str, Any]:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", content, flags=re.DOTALL)
        if not match:
            raise DeepSeekReportError("DeepSeek response did not contain a JSON object.") from None
        parsed = json.loads(match.group(0))

    if not isinstance(parsed, dict):
        raise DeepSeekReportError("DeepSeek response JSON was not an object.")
    return parsed


def _normalise_report(parsed: dict[str, Any], fallback_report: dict[str, Any], model: str) -> dict[str, Any]:
    structured_summary = parsed.get("structuredSummary") or fallback_report.get("structuredSummary", {})
    fallback_structured_summary = fallback_report.get("structuredSummary", {})
    if not isinstance(structured_summary, dict):
        structured_summary = fallback_structured_summary

    structured_summary = {
        "overallAssessment": structured_summary.get("overallAssessment")
        or fallback_structured_summary.get("overallAssessment")
        or fallback_report.get("summary"),
        "mainBehaviouralPattern": structured_summary.get("mainBehaviouralPattern")
        or fallback_structured_summary.get("mainBehaviouralPattern"),
        "routeContextExplanation": structured_summary.get("routeContextExplanation")
        or fallback_structured_summary.get("routeContextExplanation"),
        "whyItMatters": structured_summary.get("whyItMatters") or fallback_structured_summary.get("whyItMatters"),
        "nextDriveFocus": structured_summary.get("nextDriveFocus")
        or fallback_structured_summary.get("nextDriveFocus")
        or fallback_report.get("nextSessionFocus", []),
    }
    if not isinstance(structured_summary["nextDriveFocus"], list):
        structured_summary["nextDriveFocus"] = fallback_structured_summary.get("nextDriveFocus", [])

    report = {
        "summary": parsed.get("summary") or structured_summary["overallAssessment"] or fallback_report.get("summary"),
        "structuredSummary": structured_summary,
        "keyFindings": parsed.get("keyFindings") or fallback_report.get("keyFindings", []),
        "behaviourInsight": parsed.get("behaviourInsight") or fallback_report.get("behaviourInsight"),
        "driverStateInsight": parsed.get("driverStateInsight") or fallback_report.get("driverStateInsight"),
        "nextSessionFocus": parsed.get("nextSessionFocus") or fallback_report.get("nextSessionFocus", []),
        "eventSuggestions": parsed.get("eventSuggestions") or fallback_report.get("eventSuggestions", []),
        "evidenceUsed": fallback_report.get("evidenceUsed", []),
        "retrievedKnowledge": fallback_report.get("retrievedKnowledge", []),
        "agentMode": f"deepseek_llm:{model}",
        "llmProvider": "deepseek",
        "llmModel": model,
        "workflowEngine": fallback_report.get("workflowEngine"),
        "workflowNodes": fallback_report.get("workflowNodes", []),
        "evidencePolicy": fallback_report.get("evidencePolicy"),
        "sessionId": fallback_report.get("sessionId"),
    }

    if not isinstance(report["keyFindings"], list):
        report["keyFindings"] = fallback_report.get("keyFindings", [])
    if not isinstance(report["nextSessionFocus"], list):
        report["nextSessionFocus"] = fallback_report.get("nextSessionFocus", [])
    if not isinstance(report["eventSuggestions"], list):
        report["eventSuggestions"] = fallback_report.get("eventSuggestions", [])

    return report


def _normalise_chat_response(parsed: dict[str, Any], fallback_response: dict[str, Any], model: str) -> dict[str, Any]:
    response = {
        "answer": parsed.get("answer") or fallback_response.get("answer"),
        "evidenceUsed": parsed.get("evidenceUsed") or fallback_response.get("evidenceUsed", []),
        "coachingActions": parsed.get("coachingActions") or fallback_response.get("coachingActions", []),
        "confidence": parsed.get("confidence") or fallback_response.get("confidence", "medium"),
        "safetyNotes": parsed.get("safetyNotes") or fallback_response.get("safetyNotes", []),
        "followUpQuestions": parsed.get("followUpQuestions") or fallback_response.get("followUpQuestions", []),
        "agentMode": f"deepseek_llm:{model}",
        "retrievedKnowledge": fallback_response.get("retrievedKnowledge", []),
    }

    for field in ["evidenceUsed", "coachingActions", "safetyNotes", "followUpQuestions"]:
        if not isinstance(response[field], list):
            response[field] = fallback_response.get(field, [])

    if response["confidence"] not in {"low", "medium", "high"}:
        response["confidence"] = fallback_response.get("confidence", "medium")

    return response


def generate_deepseek_report(state: dict[str, Any], fallback_report: dict[str, Any]) -> dict[str, Any]:
    if OpenAI is None:
        raise DeepSeekReportError("OpenAI SDK is not installed.")

    api_key = _get_env("DEEPSEEK_API_KEY")
    if not api_key:
        raise DeepSeekReportError("DEEPSEEK_API_KEY is not configured.")

    model = _get_env("DEEPSEEK_MODEL", DEEPSEEK_DEFAULT_MODEL) or DEEPSEEK_DEFAULT_MODEL
    base_url = _get_env("DEEPSEEK_BASE_URL", DEEPSEEK_BASE_URL) or DEEPSEEK_BASE_URL
    client = OpenAI(api_key=api_key, base_url=base_url)
    payload = _build_llm_payload(state, fallback_report)

    messages = [
        {
            "role": "system",
            "content": (
                "You are DriveCoach AI, a post-drive coaching assistant for connected-vehicle telemetry. "
                "You explain deterministic driving metrics and rule-based risk events in clear, practical language. "
                "Do not make medical, fatigue, stress, diagnosis, or health claims. "
                "Return only valid JSON."
            ),
        },
        {
            "role": "user",
            "content": (
                "Generate a concise coaching report from this evidence using a fixed product template. "
                "Return a JSON object with exactly these fields: "
                "summary: string; "
                "structuredSummary: {overallAssessment: string, mainBehaviouralPattern: string, "
                "routeContextExplanation: string, whyItMatters: string, nextDriveFocus: string[]}; "
                "keyFindings: string[]; behaviourInsight: string; driverStateInsight: string; nextSessionFocus: string[]; "
                "eventSuggestions: {eventId?: string, type?: string, segmentName?: string, severity?: string, suggestion?: string}[]. "
                "Template rules: overallAssessment should be one sentence and not just repeat the score; "
                "mainBehaviouralPattern should identify the dominant pattern such as late braking, corner entry speed, "
                "lateral demand, or speed fluctuation; routeContextExplanation must mention the Cranfield to Milton Keynes "
                "route context or equivalent route segments; whyItMatters should explain comfort, stability, and predictability "
                "without medical or safety exaggeration; nextDriveFocus should contain 2-3 concrete coaching actions. "
                "Do not invent evidence. Base every statement on the supplied deterministic metrics, route, events, "
                "and retrieved knowledge snippets."
                "\n\nEvidence:\n"
                f"{json.dumps(payload, ensure_ascii=False)}"
            ),
        },
    ]

    completion_args: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "stream": False,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    reasoning_effort = _get_env("DEEPSEEK_REASONING_EFFORT")
    if reasoning_effort:
        completion_args["reasoning_effort"] = reasoning_effort

    if (_get_env("DEEPSEEK_THINKING_ENABLED", "") or "").lower() in {"1", "true", "yes"}:
        completion_args["extra_body"] = {"thinking": {"type": "enabled"}}

    response = client.chat.completions.create(**completion_args)
    content = response.choices[0].message.content
    if not content:
        raise DeepSeekReportError("DeepSeek returned an empty response.")

    return _normalise_report(_extract_json(content), fallback_report, model)


def generate_deepseek_chat_response(
    trip: dict[str, Any],
    messages: list[dict[str, str]],
    selected_event: dict[str, Any] | None,
    knowledge_snippets: list[dict[str, Any]],
    fallback_response: dict[str, Any],
) -> dict[str, Any]:
    if OpenAI is None:
        raise DeepSeekReportError("OpenAI SDK is not installed.")

    api_key = _get_env("DEEPSEEK_API_KEY")
    if not api_key:
        raise DeepSeekReportError("DEEPSEEK_API_KEY is not configured.")

    model = _get_env("DEEPSEEK_MODEL", DEEPSEEK_DEFAULT_MODEL) or DEEPSEEK_DEFAULT_MODEL
    base_url = _get_env("DEEPSEEK_BASE_URL", DEEPSEEK_BASE_URL) or DEEPSEEK_BASE_URL
    client = OpenAI(api_key=api_key, base_url=base_url)

    metrics = trip.get("metrics", {})
    payload = {
        "route": trip.get("route", {}),
        "metrics": {
            "overallDrivingScore": metrics.get("overallDrivingScore"),
            "contextAdaptationScore": metrics.get("contextAdaptationScore"),
            "riskEventCount": metrics.get("riskEventCount"),
            "wearableConnected": metrics.get("wearableConnected"),
            "meanHeartRate": metrics.get("meanHeartRate"),
            "maxHeartRate": metrics.get("maxHeartRate"),
            "baselineHeartRate": metrics.get("baselineHeartRate"),
            "heartRateDeltaPercent": metrics.get("heartRateDeltaPercent"),
        },
        "events": _compact_events(trip.get("events", [])),
        "selectedEvent": selected_event,
        "knowledgeSnippets": knowledge_snippets,
        "fallbackResponse": fallback_response,
    }

    chat_messages = [
        {
            "role": "system",
            "content": (
                "You are DriveCoach AI, an evidence-grounded post-drive coaching assistant. "
                "Answer the user's follow-up using only the supplied trip evidence and knowledge snippets. "
                "Be concise, practical, and non-judgmental. Do not make medical, stress, fatigue, or health claims. "
                "Return only valid JSON."
            ),
        },
        {
            "role": "user",
            "content": (
                "Trip evidence and retrieved coaching knowledge:\n"
                f"{json.dumps(payload, ensure_ascii=False)}\n\n"
                "Conversation so far:\n"
                f"{json.dumps(messages[-8:], ensure_ascii=False)}\n\n"
                "Return a JSON object with exactly these fields: "
                "answer: string; evidenceUsed: {type: string, label: string, value?: string}[]; "
                "coachingActions: string[]; confidence: 'low'|'medium'|'high'; "
                "safetyNotes: string[]; followUpQuestions: string[]."
            ),
        },
    ]

    completion_args: dict[str, Any] = {
        "model": model,
        "messages": chat_messages,
        "stream": False,
        "temperature": 0.25,
        "response_format": {"type": "json_object"},
    }

    reasoning_effort = _get_env("DEEPSEEK_REASONING_EFFORT")
    if reasoning_effort:
        completion_args["reasoning_effort"] = reasoning_effort

    if (_get_env("DEEPSEEK_THINKING_ENABLED", "") or "").lower() in {"1", "true", "yes"}:
        completion_args["extra_body"] = {"thinking": {"type": "enabled"}}

    response = client.chat.completions.create(**completion_args)
    content = response.choices[0].message.content
    if not content:
        raise DeepSeekReportError("DeepSeek returned an empty response.")

    return _normalise_chat_response(_extract_json(content), fallback_response, model)
