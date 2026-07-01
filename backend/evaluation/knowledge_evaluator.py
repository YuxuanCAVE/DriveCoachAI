from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.agent.knowledge import load_knowledge_snippets, retrieve_knowledge_snippets
from backend.services.demo_session_service import EVENT_SPECS, ROUTE


REQUIRED_SCHEMA_FIELDS = [
    "id",
    "title",
    "eventTypes",
    "keywords",
    "source",
    "confidence",
    "version",
    "appliesTo",
    "doSay",
    "doNotSay",
    "body",
]

REQUIRED_POLICY_IDS = {
    "evidence_first_coaching",
    "wearable_context_policy",
    "driver_assistance_scope",
}

ALLOWED_INTERNAL_SOURCES = {
    "internal_product_policy",
    "supplied_route_reference_image",
}


def _check(id_: str, passed: bool, detail: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"id": id_, "passed": passed, "detail": detail}
    if metadata is not None:
        result["metadata"] = metadata
    return result


def _valid_source(source: str) -> bool:
    return source in ALLOWED_INTERNAL_SOURCES or source.startswith("https://")


def _event_type_coverage(snippets: list[dict[str, Any]]) -> dict[str, Any]:
    expected = sorted({spec["type"] for spec in EVENT_SPECS})
    covered = set()
    for snippet in snippets:
        event_types = snippet.get("eventTypes", [])
        if "*" in event_types:
            continue
        covered.update(str(event_type) for event_type in event_types)

    missing = [event_type for event_type in expected if event_type not in covered]
    return {
        "expected": expected,
        "covered": sorted(covered.intersection(expected)),
        "missing": missing,
        "coverageRatio": 1.0 if not expected else round((len(expected) - len(missing)) / len(expected), 3),
    }


def _retrieval_case(event_type: str, segment_name: str, question: str | None = None) -> dict[str, Any]:
    event = {
        "id": f"eval-{event_type}",
        "type": event_type,
        "severity": "medium",
        "segmentName": segment_name,
        "startTime": 240,
        "endTime": 245,
    }
    snippets = retrieve_knowledge_snippets(
        [event],
        selected_event=event,
        question=question or f"What should I do about {event_type.replace('_', ' ')}?",
        route_context=ROUTE,
        metrics={"wearableConnected": "heart" in (question or "").lower()},
        limit=5,
    )
    matched_token = f"event_type:{event_type}"
    has_event_match = any(matched_token in snippet.get("matchedBy", []) for snippet in snippets)
    explainable = all(snippet.get("whyUsed") and snippet.get("matchedBy") and snippet.get("retrievalMode") for snippet in snippets)
    return {
        "eventType": event_type,
        "retrievedIds": [snippet.get("id") for snippet in snippets],
        "hasEventMatch": has_event_match,
        "explainable": explainable,
        "matchedBy": [match for snippet in snippets for match in snippet.get("matchedBy", [])],
    }


def _retrieval_smoke_cases() -> list[dict[str, Any]]:
    return [
        _retrieval_case("late_braking_before_curve", "North Crawley village approach"),
        _retrieval_case("high_lateral_acceleration", "Newport Road rural bend"),
        _retrieval_case("unstable_speed_control", "Milton Keynes grid-road arrival"),
        _retrieval_case("harsh_acceleration", "A422 / Monks Way junction"),
        _retrieval_case("late_braking_before_curve", "North Crawley village approach", question="How should I interpret heart rate here?"),
    ]


def evaluate_knowledge_base() -> dict[str, Any]:
    snippets = load_knowledge_snippets()
    checks: list[dict[str, Any]] = []

    ids = [snippet.get("id") for snippet in snippets]
    duplicate_ids = sorted({id_ for id_ in ids if ids.count(id_) > 1})
    checks.append(
        _check(
            "unique_knowledge_ids",
            not duplicate_ids,
            "All knowledge IDs are unique." if not duplicate_ids else f"Duplicate IDs: {', '.join(duplicate_ids)}",
            {"duplicateIds": duplicate_ids},
        )
    )

    missing_by_id = {
        str(snippet.get("id", "unknown")): [field for field in REQUIRED_SCHEMA_FIELDS if not snippet.get(field)]
        for snippet in snippets
    }
    missing_by_id = {id_: missing for id_, missing in missing_by_id.items() if missing}
    checks.append(
        _check(
            "schema_completeness",
            not missing_by_id,
            "All knowledge snippets include the required schema fields."
            if not missing_by_id
            else "One or more snippets is missing required schema fields.",
            {"missingById": missing_by_id},
        )
    )

    invalid_confidence = [
        snippet.get("id")
        for snippet in snippets
        if snippet.get("confidence") not in {"low", "medium", "high"}
    ]
    checks.append(
        _check(
            "confidence_values_valid",
            not invalid_confidence,
            "All confidence values are valid." if not invalid_confidence else f"Invalid confidence IDs: {', '.join(invalid_confidence)}",
            {"invalidIds": invalid_confidence},
        )
    )

    invalid_sources = [
        {"id": snippet.get("id"), "source": snippet.get("source")}
        for snippet in snippets
        if not _valid_source(str(snippet.get("source", "")))
    ]
    checks.append(
        _check(
            "source_provenance_present",
            not invalid_sources,
            "All knowledge snippets have accepted source provenance."
            if not invalid_sources
            else "One or more snippets has invalid source provenance.",
            {"invalidSources": invalid_sources},
        )
    )

    policy_ids = {str(snippet.get("id")) for snippet in snippets}
    missing_policy_ids = sorted(REQUIRED_POLICY_IDS - policy_ids)
    checks.append(
        _check(
            "required_policy_coverage",
            not missing_policy_ids,
            "Required evidence, wearable, and driver-assistance policies are present."
            if not missing_policy_ids
            else f"Missing required policies: {', '.join(missing_policy_ids)}",
            {"missingPolicyIds": missing_policy_ids},
        )
    )

    event_coverage = _event_type_coverage(snippets)
    checks.append(
        _check(
            "event_type_coverage",
            not event_coverage["missing"],
            "Knowledge snippets cover all rule-based event types."
            if not event_coverage["missing"]
            else f"Missing event type coverage: {', '.join(event_coverage['missing'])}",
            event_coverage,
        )
    )

    do_dont_missing = [
        snippet.get("id")
        for snippet in snippets
        if not snippet.get("doSay") or not snippet.get("doNotSay")
    ]
    checks.append(
        _check(
            "do_say_do_not_say_present",
            not do_dont_missing,
            "All snippets include doSay and doNotSay guidance."
            if not do_dont_missing
            else f"Missing do/don't guidance: {', '.join(do_dont_missing)}",
            {"missingIds": do_dont_missing},
        )
    )

    retrieval_cases = _retrieval_smoke_cases()
    failed_retrieval_cases = [
        case
        for case in retrieval_cases
        if not case["hasEventMatch"] or not case["explainable"]
    ]
    checks.append(
        _check(
            "retrieval_smoke_cases",
            not failed_retrieval_cases,
            "Retrieval smoke cases return event-matched, explainable knowledge."
            if not failed_retrieval_cases
            else "One or more retrieval smoke cases failed event matching or explainability.",
            {"cases": retrieval_cases},
        )
    )

    passed_count = sum(1 for check in checks if check["passed"])
    quality_score = round((passed_count / len(checks)) * 100) if checks else 0
    blocking_failures = [
        check["id"]
        for check in checks
        if not check["passed"]
        and check["id"] in {"schema_completeness", "unique_knowledge_ids", "source_provenance_present", "retrieval_smoke_cases"}
    ]

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "knowledgeCount": len(snippets),
        "qualityScore": quality_score,
        "passed": not blocking_failures and quality_score >= 85,
        "checks": checks,
        "blockingFailures": blocking_failures,
        "eventTypeCoverage": event_coverage,
        "retrievalCases": retrieval_cases,
        "sources": sorted({str(snippet.get("source")) for snippet in snippets}),
    }

