from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any


KNOWLEDGE_DIR = Path(__file__).resolve().parents[1] / "knowledge"
POLICY_SNIPPET_IDS = {"evidence_first_coaching", "wearable_context_policy"}


def _split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _parse_knowledge_file(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    metadata: dict[str, str] = {}
    body = text

    if text.startswith("---"):
        _, frontmatter, body = text.split("---", 2)
        for line in frontmatter.splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            metadata[key.strip()] = value.strip()

    snippet = {
        "id": metadata.get("id", path.stem),
        "title": metadata.get("title", path.stem.replace("_", " ").title()),
        "eventTypes": _split_csv(metadata.get("eventTypes", "")),
        "keywords": _split_csv(metadata.get("keywords", "")),
        "source": metadata.get("source", "internal_product_policy"),
        "confidence": metadata.get("confidence", "medium"),
        "version": metadata.get("version", "unknown"),
        "appliesTo": metadata.get("appliesTo", ""),
        "doSay": metadata.get("doSay", ""),
        "doNotSay": metadata.get("doNotSay", ""),
        "body": body.strip(),
    }
    if not snippet["eventTypes"]:
        snippet["eventTypes"] = ["*"]
    return snippet


@lru_cache(maxsize=1)
def load_knowledge_snippets() -> list[dict[str, Any]]:
    if not KNOWLEDGE_DIR.exists():
        return []

    return [_parse_knowledge_file(path) for path in sorted(KNOWLEDGE_DIR.glob("*.md"))]


def _normalise_text(*values: Any) -> str:
    return " ".join(str(value or "").lower() for value in values)


def _event_types(events: list[dict[str, Any]], selected_event: dict[str, Any] | None) -> set[str]:
    selected_types: set[str] = set()
    if selected_event and selected_event.get("type"):
        selected_types.add(str(selected_event["type"]))
    selected_types.update(str(event.get("type")) for event in events if event.get("type"))
    return selected_types


def _route_terms(route_context: dict[str, Any] | None, events: list[dict[str, Any]]) -> str:
    route = route_context or {}
    event_segments = " ".join(str(event.get("segmentName", "")) for event in events)
    return _normalise_text(
        route.get("name"),
        route.get("origin"),
        route.get("destination"),
        route.get("description"),
        event_segments,
    )


def _score_snippet(
    snippet: dict[str, Any],
    selected_types: set[str],
    query_text: str,
    route_text: str,
    has_wearable: bool,
) -> int:
    return _match_snippet(snippet, selected_types, query_text, route_text, has_wearable)["score"]


def _match_snippet(
    snippet: dict[str, Any],
    selected_types: set[str],
    query_text: str,
    route_text: str,
    has_wearable: bool,
) -> dict[str, Any]:
    snippet_id = str(snippet.get("id", ""))
    event_types = set(str(event_type) for event_type in snippet.get("eventTypes", []))
    keywords = [str(keyword).lower() for keyword in snippet.get("keywords", [])]
    searchable = _normalise_text(
        snippet.get("title"),
        snippet.get("body"),
        snippet.get("appliesTo"),
        snippet.get("doSay"),
        snippet.get("doNotSay"),
        " ".join(keywords),
    )

    score = 0
    matched_by: list[str] = []
    if snippet_id == "evidence_first_coaching":
        score += 8
        matched_by.append("policy:evidence_first")
    if snippet_id == "wearable_context_policy" and (has_wearable or "wearable" in query_text or "heart" in query_text):
        score += 8
        matched_by.append("policy:wearable_context")
    if "*" in event_types:
        score += 1
        matched_by.append("event_type:any")
    if selected_types.intersection(event_types):
        matched_events = sorted(selected_types.intersection(event_types))
        score += 10 + len(matched_events)
        matched_by.extend(f"event_type:{event_type}" for event_type in matched_events)
    for keyword in keywords:
        if keyword and keyword in query_text:
            score += 4
            matched_by.append(f"question_keyword:{keyword}")
        if keyword and keyword in route_text:
            score += 2
            matched_by.append(f"route_keyword:{keyword}")
    if "cranfield" in route_text and "cranfield" in searchable:
        score += 4
        matched_by.append("route_context:cranfield")
    if "milton keynes" in route_text and "milton keynes" in searchable:
        score += 4
        matched_by.append("route_context:milton_keynes")

    unique_matches = list(dict.fromkeys(matched_by))
    return {
        "score": score,
        "matchedBy": unique_matches,
        "whyUsed": _why_used(snippet, unique_matches),
    }


def _why_used(snippet: dict[str, Any], matched_by: list[str]) -> str:
    title = str(snippet.get("title", "Knowledge"))
    event_matches = [match.split(":", 1)[1].replace("_", " ") for match in matched_by if match.startswith("event_type:") and match != "event_type:any"]
    route_matches = [match.split(":", 1)[1].replace("_", " ") for match in matched_by if match.startswith("route_context:") or match.startswith("route_keyword:")]
    policy_matches = [match.split(":", 1)[1].replace("_", " ") for match in matched_by if match.startswith("policy:")]
    question_matches = [match.split(":", 1)[1].replace("_", " ") for match in matched_by if match.startswith("question_keyword:")]

    if event_matches:
        return f"Selected '{title}' because it matches detected event type(s): {', '.join(event_matches[:3])}."
    if route_matches:
        return f"Selected '{title}' because it matches the reviewed route context: {', '.join(route_matches[:3])}."
    if question_matches:
        return f"Selected '{title}' because it matches the user's question keyword(s): {', '.join(question_matches[:3])}."
    if policy_matches:
        return f"Selected '{title}' because it is a required coaching policy: {', '.join(policy_matches[:2])}."
    return f"Selected '{title}' as supporting DriveCoach knowledge."


def retrieve_knowledge_snippets(
    events: list[dict[str, Any]],
    selected_event: dict[str, Any] | None = None,
    question: str | None = None,
    route_context: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    snippets = load_knowledge_snippets()
    if not snippets:
        return []

    selected_types = _event_types(events, selected_event)
    query_text = _normalise_text(question)
    route_text = _route_terms(route_context, events)
    has_wearable = bool((metrics or {}).get("wearableConnected", False))

    scored = []
    for index, snippet in enumerate(snippets):
        match = _match_snippet(snippet, selected_types, query_text, route_text, has_wearable)
        scored.append((match["score"], index, snippet, match))
    ranked = [
        (snippet, match)
        for score, _, snippet, match in sorted(scored, key=lambda item: (-item[0], item[1]))
        if score > 0
    ]

    policy_snippets = [(snippet, match) for snippet, match in ranked if snippet["id"] in POLICY_SNIPPET_IDS]
    domain_snippets = [(snippet, match) for snippet, match in ranked if snippet["id"] not in POLICY_SNIPPET_IDS]
    selected = (policy_snippets[:2] + domain_snippets)[:limit]

    return [
        {
            "id": snippet["id"],
            "title": snippet["title"],
            "eventTypes": snippet["eventTypes"],
            "keywords": snippet["keywords"],
            "source": snippet["source"],
            "confidence": snippet["confidence"],
            "version": snippet["version"],
            "appliesTo": snippet["appliesTo"],
            "doSay": snippet["doSay"],
            "doNotSay": snippet["doNotSay"],
            "matchedBy": match["matchedBy"],
            "whyUsed": match["whyUsed"],
            "retrievalMode": "rag_lite_explainable",
            "score": match["score"],
            "body": snippet["body"],
        }
        for snippet, match in selected
    ]


def select_knowledge_snippets(events: list[dict[str, Any]], selected_event: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    return retrieve_knowledge_snippets(events, selected_event=selected_event)
