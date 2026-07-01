from __future__ import annotations

from functools import lru_cache
from typing import Any

from langgraph.graph import END, START, StateGraph

from backend.agent.coach_workflow import (
    analyse_evidence_node,
    generate_report_node,
    load_session_node,
    retrieve_knowledge_node,
    revise_report_node,
    should_revise_report,
    validate_report_node,
)
from backend.agent.state import CoachAgentState


LANGGRAPH_NODE_NAMES = [
    "LoadTripNode",
    "AnalyseEvidenceNode",
    "RetrieveKnowledgeNode",
    "GenerateCoachReportNode",
    "ValidateReportNode",
    "ReviseReportNode",
]


@lru_cache(maxsize=1)
def build_coach_graph() -> Any:
    graph = StateGraph(CoachAgentState)

    graph.add_node("LoadTripNode", load_session_node)
    graph.add_node("AnalyseEvidenceNode", analyse_evidence_node)
    graph.add_node("RetrieveKnowledgeNode", retrieve_knowledge_node)
    graph.add_node("GenerateCoachReportNode", generate_report_node)
    graph.add_node("ValidateReportNode", validate_report_node)
    graph.add_node("ReviseReportNode", revise_report_node)

    graph.add_edge(START, "LoadTripNode")
    graph.add_edge("LoadTripNode", "AnalyseEvidenceNode")
    graph.add_edge("AnalyseEvidenceNode", "RetrieveKnowledgeNode")
    graph.add_edge("RetrieveKnowledgeNode", "GenerateCoachReportNode")
    graph.add_edge("GenerateCoachReportNode", "ValidateReportNode")
    graph.add_conditional_edges(
        "ValidateReportNode",
        should_revise_report,
        {
            "revise": "ReviseReportNode",
            "return": END,
        },
    )
    graph.add_edge("ReviseReportNode", "ValidateReportNode")

    return graph.compile()


def run_langgraph_coach_workflow(trip: dict[str, Any]) -> dict[str, Any]:
    app = build_coach_graph()
    final_state = app.invoke(
        {
            "trip": trip,
            "workflow_engine": "langgraph",
            "workflow_nodes": LANGGRAPH_NODE_NAMES,
            "mode": "langgraph_deterministic_agent_no_llm",
        }
    )
    report = final_state["report"]
    return {
        **report,
        "workflowEngine": "langgraph",
        "workflowNodes": LANGGRAPH_NODE_NAMES,
    }
