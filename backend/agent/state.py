from __future__ import annotations

from typing import Any, TypedDict


class CoachAgentState(TypedDict, total=False):
    """LangGraph-ready state container for the deterministic coach workflow."""

    trip: dict[str, Any]
    route_context: dict[str, Any]
    metrics: dict[str, Any]
    events: list[dict[str, Any]]
    evidence_summary: dict[str, Any]
    guidance_context: list[str]
    retrieved_knowledge: list[dict[str, Any]]
    report: dict[str, Any]
    validation_notes: list[str]
    report_validation: dict[str, Any]
    revision_count: int
    mode: str
    workflow_engine: str
    workflow_nodes: list[str]
