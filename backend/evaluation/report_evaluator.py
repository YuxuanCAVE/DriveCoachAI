from __future__ import annotations

import re
from typing import Any


UNSUPPORTED_MEDICAL_TERMS = [
    "diagnosis",
    "diagnose",
    "disease",
    "medical condition",
    "fatigue detected",
    "stress detected",
    "health risk",
]

REQUIRED_REPORT_FIELDS = [
    "summary",
    "structuredSummary",
    "keyFindings",
    "behaviourInsight",
    "nextSessionFocus",
    "evidenceUsed",
    "retrievedKnowledge",
]


def _text(report: dict[str, Any]) -> str:
    return str(report).lower()


def _clamp_score(value: float) -> int:
    return max(0, min(100, round(value)))


def _extract_report_sections(report: dict[str, Any]) -> dict[str, str]:
    structured = report.get("structuredSummary", {})
    structured_next_focus = structured.get("nextDriveFocus", []) if isinstance(structured, dict) else []
    event_suggestions = report.get("eventSuggestions", [])
    return {
        "summary": str(report.get("summary", "")),
        "key_findings": " ".join(str(item) for item in report.get("keyFindings", [])),
        "behaviour": str(report.get("behaviourInsight", "")),
        "next_focus": " ".join(str(item) for item in report.get("nextSessionFocus", []))
        + " "
        + " ".join(str(item) for item in structured_next_focus),
        "route_context": str(structured.get("routeContextExplanation", "")) if isinstance(structured, dict) else "",
        "why_it_matters": str(structured.get("whyItMatters", "")) if isinstance(structured, dict) else "",
        "event_suggestions": " ".join(
            str(item.get("suggestion", item)) if isinstance(item, dict) else str(item) for item in event_suggestions
        ),
    }


def _word_count(text: str) -> int:
    return len(re.findall(r"[A-Za-z][A-Za-z'-]*|\d+(?:\.\d+)?", text))


def _count_matches(text: str, patterns: list[str]) -> int:
    return sum(1 for pattern in patterns if re.search(pattern, text, flags=re.IGNORECASE))


def _contains_route_context(report: dict[str, Any], trip: dict[str, Any]) -> bool:
    route = trip.get("route", {})
    route_terms = [
        str(route.get("origin", "")).lower(),
        str(route.get("destination", "")).lower(),
        "cranfield",
        "milton keynes",
    ]
    report_text = _text(report)
    return any(term and term in report_text for term in route_terms)


def _event_coverage(report: dict[str, Any], trip: dict[str, Any]) -> dict[str, Any]:
    report_text = _text(report)
    events = trip.get("events", [])
    covered = []
    missing = []

    for event in events[:4]:
        event_type = str(event.get("type", ""))
        readable_type = event_type.replace("_", " ")
        segment_name = str(event.get("segmentName", ""))
        is_covered = event_type in report_text or readable_type in report_text or segment_name.lower() in report_text
        target = event_type or segment_name or "event"
        if is_covered:
            covered.append(target)
        else:
            missing.append(target)

    return {
        "covered": covered,
        "missing": missing,
        "coverageRatio": 1.0 if not events else round(len(covered) / min(len(events), 4), 3),
    }


def _knowledge_coverage(report: dict[str, Any], trip: dict[str, Any]) -> dict[str, Any]:
    knowledge = [item for item in report.get("retrievedKnowledge", []) if isinstance(item, dict)]
    event_types = [str(event.get("type", "")) for event in trip.get("events", [])[:4] if event.get("type")]
    matched_by = [match for item in knowledge for match in item.get("matchedBy", []) if isinstance(match, str)]
    covered = []
    missing = []

    for event_type in event_types:
        token = f"event_type:{event_type}"
        if token in matched_by:
            covered.append(event_type)
        else:
            missing.append(event_type)

    explainable_items = [
        item
        for item in knowledge
        if item.get("whyUsed") and item.get("matchedBy") and item.get("retrievalMode")
    ]
    return {
        "covered": covered,
        "missing": missing,
        "explainableCount": len(explainable_items),
        "retrievedCount": len(knowledge),
        "coverageRatio": 1.0 if not event_types else round(len(covered) / len(event_types), 3),
    }


def _suggestion_specificity(report: dict[str, Any], trip: dict[str, Any]) -> dict[str, Any]:
    sections = _extract_report_sections(report)
    focus_text = f"{sections['next_focus']} {sections['event_suggestions']}".strip()
    events = trip.get("events", [])
    event_terms = {str(event.get("type", "")).replace("_", " ") for event in events if event.get("type")}
    segment_terms = {str(event.get("segmentName", "")) for event in events if event.get("segmentName")}

    action_terms = [
        r"\bbrake\b",
        r"\breduce\b",
        r"\blower\b",
        r"\bhold\b",
        r"\bmaintain\b",
        r"\bkeep\b",
        r"\breview\b",
        r"\bsmooth(?:er|ly)?\b",
        r"\bprogressive(?:ly)?\b",
        r"\bsteer(?:ing)?\b",
        r"\bthrottle\b",
        r"\bentry speed\b",
        r"\bfollowing\b",
    ]
    context_terms = [
        r"\bbefore\b",
        r"\bafter\b",
        r"\bcurve\b",
        r"\bbend\b",
        r"\bjunction\b",
        r"\burban\b",
        r"\brural\b",
        r"\broute\b",
        r"\bsegment\b",
        r"\barrival\b",
        r"\bcampus\b",
    ]

    action_count = _count_matches(focus_text, action_terms)
    context_count = _count_matches(focus_text, context_terms)
    event_reference_count = sum(1 for term in event_terms if term and term in focus_text.lower())
    segment_reference_count = sum(1 for term in segment_terms if term and term.lower() in focus_text.lower())
    useful_length = 12 <= _word_count(focus_text) <= 180

    score = 20
    score += min(action_count, 5) * 10
    score += min(context_count, 4) * 6
    score += min(event_reference_count + segment_reference_count, 3) * 8
    if useful_length:
        score += 10

    return {
        "id": "suggestion_specificity",
        "score": _clamp_score(score),
        "passed": score >= 70,
        "detail": (
            "Coaching suggestions include concrete actions and route/event context."
            if score >= 70
            else "Coaching suggestions are too generic or lack route/event-specific action language."
        ),
        "metadata": {
            "actionTermCount": action_count,
            "contextTermCount": context_count,
            "eventReferenceCount": event_reference_count,
            "segmentReferenceCount": segment_reference_count,
            "wordCount": _word_count(focus_text),
        },
    }


def _target_measurability(report: dict[str, Any], trip: dict[str, Any]) -> dict[str, Any]:
    sections = _extract_report_sections(report)
    relevant_text = f"{sections['next_focus']} {sections['key_findings']} {sections['event_suggestions']}"
    evidence = [item for item in report.get("evidenceUsed", []) if isinstance(item, dict)]
    numeric_evidence_count = sum(1 for item in evidence if re.search(r"\d", str(item.get("value", ""))))
    measurement_terms = _count_matches(
        relevant_text,
        [
            r"\bscore\b",
            r"\bevent(?:s)?\b",
            r"\bcount\b",
            r"\bmax(?:imum)?\b",
            r"\bmean\b",
            r"\bspeed\b",
            r"\bbraking\b",
            r"\blateral\b",
            r"\byaw\b",
            r"\bacceleration\b",
            r"\btarget\b",
            r"\bthreshold\b",
        ],
    )
    has_next_focus = bool(report.get("nextSessionFocus"))
    score = 25 + min(numeric_evidence_count, 4) * 10 + min(measurement_terms, 6) * 6
    if has_next_focus:
        score += 15

    return {
        "id": "target_measurability",
        "score": _clamp_score(score),
        "passed": score >= 70,
        "detail": (
            "The report links next-drive focus to observable metrics, events, or vehicle signals."
            if score >= 70
            else "The report does not make the coaching target easy enough to measure next time."
        ),
        "metadata": {
            "numericEvidenceCount": numeric_evidence_count,
            "measurementTermCount": measurement_terms,
            "hasNextSessionFocus": has_next_focus,
        },
    }


def _route_context_relevance(report: dict[str, Any], trip: dict[str, Any], event_coverage: dict[str, Any]) -> dict[str, Any]:
    sections = _extract_report_sections(report)
    report_text = _text(report)
    route = trip.get("route", {})
    route_terms = [
        route.get("origin"),
        route.get("destination"),
        route.get("name"),
        "cranfield",
        "milton keynes",
        "rural",
        "urban",
        "junction",
        "bend",
        "curve",
        "campus",
        "arrival",
    ]
    route_term_count = sum(1 for term in route_terms if term and str(term).lower() in report_text)
    segment_terms = {str(event.get("segmentName", "")) for event in trip.get("events", []) if event.get("segmentName")}
    segment_count = sum(1 for term in segment_terms if term and term.lower() in report_text)
    has_route_section = _word_count(sections["route_context"]) >= 12
    score = 20 + min(route_term_count, 6) * 8 + min(segment_count, 3) * 8 + round(event_coverage["coverageRatio"] * 8)
    if has_route_section:
        score += 10

    return {
        "id": "route_context_relevance",
        "score": _clamp_score(score),
        "passed": score >= 70,
        "detail": (
            "The report connects coaching to the route and relevant driving contexts."
            if score >= 70
            else "The report is not route-aware enough for this session."
        ),
        "metadata": {
            "routeTermCount": route_term_count,
            "segmentReferenceCount": segment_count,
            "eventCoverageRatio": event_coverage["coverageRatio"],
            "hasRouteContextSection": has_route_section,
        },
    }


def _no_overclaim_score(report: dict[str, Any]) -> dict[str, Any]:
    report_text = _text(report)
    unsupported_terms = [term for term in UNSUPPORTED_MEDICAL_TERMS if re.search(rf"\b{re.escape(term)}\b", report_text)]
    overclaim_patterns = [
        r"\bguarantee(?:s|d)?\b",
        r"\bprove(?:s|d)?\b",
        r"\bwill prevent\b",
        r"\bunsafe driver\b",
        r"\bdangerous driver\b",
        r"\bmust be\b",
        r"\balways\b",
        r"\bnever\b",
    ]
    overclaim_count = _count_matches(report_text, overclaim_patterns)
    score = 100 - len(unsupported_terms) * 30 - overclaim_count * 10

    return {
        "id": "no_overclaim_score",
        "score": _clamp_score(score),
        "passed": score >= 85,
        "detail": (
            "The report stays within evidence and avoids unsupported claims."
            if score >= 85
            else "The report contains language that may overstate what telemetry evidence can support."
        ),
        "metadata": {
            "unsupportedMedicalTerms": unsupported_terms,
            "overclaimPatternCount": overclaim_count,
        },
    }


def _coach_usefulness_score(dimensions: list[dict[str, Any]], event_coverage: dict[str, Any], knowledge_coverage: dict[str, Any]) -> dict[str, Any]:
    dimension_scores = {dimension["id"]: int(dimension["score"]) for dimension in dimensions}
    base_score = (
        dimension_scores["suggestion_specificity"] * 0.28
        + dimension_scores["target_measurability"] * 0.22
        + dimension_scores["route_context_relevance"] * 0.24
        + dimension_scores["no_overclaim_score"] * 0.16
        + round(event_coverage["coverageRatio"] * 100) * 0.05
        + round(knowledge_coverage["coverageRatio"] * 100) * 0.05
    )
    score = _clamp_score(base_score)
    return {
        "id": "coach_usefulness_score",
        "score": score,
        "passed": score >= 75,
        "detail": (
            "The coach output is specific, measurable, route-aware, and evidence-bounded."
            if score >= 75
            else "The coach output needs more actionable, measurable, or route-specific guidance."
        ),
        "metadata": {
            "eventCoverageRatio": event_coverage["coverageRatio"],
            "knowledgeCoverageRatio": knowledge_coverage["coverageRatio"],
            "componentScores": dimension_scores,
        },
    }


def evaluate_coach_report(report: dict[str, Any], trip: dict[str, Any], duration_ms: int | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    missing_fields = [field for field in REQUIRED_REPORT_FIELDS if not report.get(field)]
    checks.append(
        {
            "id": "schema_completeness",
            "passed": not missing_fields,
            "detail": "All required report fields are present." if not missing_fields else f"Missing fields: {', '.join(missing_fields)}",
        }
    )

    evidence_used = report.get("evidenceUsed", [])
    evidence_types = {item.get("type") for item in evidence_used if isinstance(item, dict)}
    has_metric_evidence = "metric" in evidence_types
    checks.append(
        {
            "id": "metric_evidence_present",
            "passed": has_metric_evidence,
            "detail": "Report includes deterministic metric evidence." if has_metric_evidence else "Report lacks metric evidence.",
        }
    )

    knowledge = report.get("retrievedKnowledge", [])
    has_knowledge = bool(knowledge)
    checks.append(
        {
            "id": "knowledge_grounding_present",
            "passed": has_knowledge,
            "detail": "Report includes retrieved knowledge snippets." if has_knowledge else "Report lacks retrieved knowledge.",
        }
    )

    knowledge_coverage = _knowledge_coverage(report, trip)
    checks.append(
        {
            "id": "retrieval_explainability_present",
            "passed": knowledge_coverage["retrievedCount"] > 0
            and knowledge_coverage["explainableCount"] == knowledge_coverage["retrievedCount"],
            "detail": (
                "All retrieved knowledge snippets include match explanations."
                if knowledge_coverage["retrievedCount"] > 0
                and knowledge_coverage["explainableCount"] == knowledge_coverage["retrievedCount"]
                else "One or more retrieved knowledge snippets lacks matchedBy, whyUsed, or retrievalMode."
            ),
            "metadata": knowledge_coverage,
        }
    )

    checks.append(
        {
            "id": "knowledge_event_type_coverage",
            "passed": not knowledge_coverage["missing"],
            "detail": (
                "Retrieved knowledge covers the top detected event types."
                if not knowledge_coverage["missing"]
                else f"Missing knowledge coverage for event types: {', '.join(knowledge_coverage['missing'])}"
            ),
            "metadata": knowledge_coverage,
        }
    )

    has_route_context = _contains_route_context(report, trip)
    checks.append(
        {
            "id": "route_context_present",
            "passed": has_route_context,
            "detail": "Report references the reviewed route context." if has_route_context else "Report does not reference route context.",
        }
    )

    event_coverage = _event_coverage(report, trip)
    checks.append(
        {
            "id": "event_coverage",
            "passed": not event_coverage["missing"],
            "detail": (
                "Top detected events are reflected in the report."
                if not event_coverage["missing"]
                else f"Missing top event references: {', '.join(event_coverage['missing'])}"
            ),
            "metadata": event_coverage,
        }
    )

    report_text = _text(report)
    unsupported_terms = [term for term in UNSUPPORTED_MEDICAL_TERMS if re.search(rf"\b{re.escape(term)}\b", report_text)]
    checks.append(
        {
            "id": "no_unsupported_medical_claims",
            "passed": not unsupported_terms,
            "detail": (
                "No unsupported medical, fatigue, or stress diagnosis language detected."
                if not unsupported_terms
                else f"Unsupported terms found: {', '.join(unsupported_terms)}"
            ),
        }
    )

    quality_dimensions = [
        _suggestion_specificity(report, trip),
        _target_measurability(report, trip),
        _route_context_relevance(report, trip, event_coverage),
        _no_overclaim_score(report),
    ]
    coach_usefulness = _coach_usefulness_score(quality_dimensions, event_coverage, knowledge_coverage)
    quality_dimensions.append(coach_usefulness)

    checks.extend(
        {
            "id": dimension["id"],
            "passed": dimension["passed"],
            "detail": dimension["detail"],
            "metadata": dimension["metadata"],
        }
        for dimension in quality_dimensions
    )

    passed_count = sum(1 for check in checks if check["passed"])
    structural_score = round((passed_count / len(checks)) * 100)
    quality_score = _clamp_score(structural_score * 0.55 + coach_usefulness["score"] * 0.45)
    blocking_failures = [check["id"] for check in checks if not check["passed"] and check["id"] in {"schema_completeness", "no_unsupported_medical_claims"}]

    return {
        "qualityScore": quality_score,
        "structuralScore": structural_score,
        "coachUsefulnessScore": coach_usefulness["score"],
        "passed": not blocking_failures and quality_score >= 75,
        "checks": checks,
        "qualityDimensions": quality_dimensions,
        "durationMs": duration_ms,
        "blockingFailures": blocking_failures,
    }
