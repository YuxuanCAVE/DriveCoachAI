from fastapi.testclient import TestClient
from pathlib import Path

from backend.agent.coach_workflow import revise_report_node, should_revise_report, validate_report_node
from backend.agent.state import CoachAgentState
from backend.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_demo_session_endpoint_returns_frontend_compatible_trip() -> None:
    response = client.post("/api/demo-session", json={"includeWearableData": True, "seed": 1234})

    assert response.status_code == 200
    trip = response.json()
    assert trip["id"] == "cranfield-mk-mixed_route_review-1234"
    assert trip["route"]["origin"] == "Cranfield University"
    assert trip["route"]["destination"] == "Milton Keynes Midsummer Place"
    assert len(trip["samples"]) > 100
    assert len(trip["events"]) > 0
    assert trip["metrics"]["riskEventCount"] == len(trip["events"])
    assert trip["metrics"]["wearableConnected"] is True
    assert "heartRate" in trip["samples"][0]


def test_scenarios_endpoint_returns_ground_truth_scenarios() -> None:
    response = client.get("/api/scenarios")

    assert response.status_code == 200
    scenarios = response.json()
    keys = {scenario["key"] for scenario in scenarios}
    assert {
        "agent_generated",
        "smooth_baseline",
        "harsh_braking",
        "high_lateral_acceleration",
        "unstable_speed_control",
        "wearable_connected",
        "wearable_not_connected",
    }.issubset(keys)


def test_agent_generated_scenario_returns_seeded_random_trip() -> None:
    response = client.post("/api/demo-session", json={"scenario": "agent_generated", "seed": 7777})

    assert response.status_code == 200
    trip = response.json()
    assert trip["id"] == "cranfield-mk-agent_generated-7777"
    assert trip["scenario"]["key"] == "agent_generated"
    assert trip["scenario"]["generationMode"] == "seeded_random"
    assert len(trip["samples"]) > 100
    assert trip["metrics"]["riskEventCount"] == len(trip["events"])


def test_ground_truth_scenarios_are_stable_and_route_contextual() -> None:
    expectations = {
        "smooth_baseline": {"seed": 3101, "events": set(), "wearable": False},
        "harsh_braking": {"seed": 3201, "events": {"late_braking_before_curve"}, "wearable": False},
        "high_lateral_acceleration": {"seed": 3301, "events": {"high_lateral_acceleration", "unstable_cornering"}, "wearable": False},
        "unstable_speed_control": {"seed": 3401, "events": {"unstable_speed_control"}, "wearable": False},
        "wearable_connected": {"seed": 3501, "events": {"late_braking_before_curve"}, "wearable": True},
        "wearable_not_connected": {"seed": 3601, "events": {"late_braking_before_curve"}, "wearable": False},
    }

    for scenario, expected in expectations.items():
        response = client.post("/api/demo-session", json={"scenario": scenario})

        assert response.status_code == 200
        trip = response.json()
        event_types = {event["type"] for event in trip["events"]}
        assert trip["scenario"]["seed"] == expected["seed"]
        assert set(expected["events"]).issubset(event_types)
        assert trip["metrics"]["wearableConnected"] is expected["wearable"]
        assert trip["route"]["origin"] == "Cranfield University"
        assert trip["route"]["destination"] == "Milton Keynes Midsummer Place"
        assert trip["scenario"]["mapAnchors"]


def test_detected_events_include_context_aware_threshold_evidence() -> None:
    response = client.post("/api/demo-session", json={"scenario": "high_lateral_acceleration"})

    assert response.status_code == 200
    trip = response.json()
    assert trip["events"]

    event = trip["events"][0]
    evidence = event["evidence"]
    assert evidence["thresholdMode"] == "context_aware_route_grounded"
    assert evidence["threshold"] > 0
    assert evidence["baseThreshold"] > 0
    assert evidence["thresholdAxis"]
    assert evidence["thresholdReason"]
    assert evidence["curvatureLevel"] in {"low", "medium", "high"}
    assert evidence["trafficComplexity"] in {"low", "medium", "high"}
    assert "speedRatioToTarget" in evidence
    assert "speedNormalisedLateralDemand" in evidence


def test_coach_report_endpoint_returns_deterministic_agent_report(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr("backend.agent.coach_workflow.is_deepseek_configured", lambda: False)
    monkeypatch.setattr("backend.evaluation.trace_store.DB_PATH", tmp_path / "agent_observability.sqlite")

    session_response = client.post("/api/demo-session", json={"scenario": "harsh_braking"})
    assert session_response.status_code == 200

    response = client.post("/api/coach-report", json={"trip": session_response.json()})

    assert response.status_code == 200
    report = response.json()
    assert report["agentMode"] in {"langgraph_deterministic_agent_no_llm", "deterministic_agent_no_llm"}
    assert report["workflowEngine"] in {"langgraph", "python_node_runner"}
    assert report["workflowNodes"] == [
        "LoadTripNode",
        "AnalyseEvidenceNode",
        "RetrieveKnowledgeNode",
        "GenerateCoachReportNode",
        "ValidateReportNode",
        "ReviseReportNode",
    ]
    assert "deterministically" in report["evidencePolicy"]
    assert report["summary"]
    assert report["structuredSummary"]["overallAssessment"]
    assert report["structuredSummary"]["mainBehaviouralPattern"]
    assert report["structuredSummary"]["routeContextExplanation"]
    assert report["structuredSummary"]["whyItMatters"]
    assert len(report["structuredSummary"]["nextDriveFocus"]) >= 2
    assert report["keyFindings"]
    assert report["behaviourInsight"]
    assert report["nextSessionFocus"]
    assert report["evidenceUsed"]
    assert report["retrievedKnowledge"]
    assert any(knowledge["source"] for knowledge in report["retrievedKnowledge"])
    assert all(knowledge["matchedBy"] for knowledge in report["retrievedKnowledge"])
    assert all(knowledge["whyUsed"] for knowledge in report["retrievedKnowledge"])
    assert all(knowledge["retrievalMode"] == "rag_lite_explainable" for knowledge in report["retrievedKnowledge"])
    assert any(evidence["type"] == "metric" for evidence in report["evidenceUsed"])
    assert any(evidence["type"] == "event" for evidence in report["evidenceUsed"])
    assert report["validationNotes"] == ["Report passed deterministic evidence and schema checks."]
    assert report["reportValidation"]["passed"] is True
    assert report["revisionApplied"] is False
    assert report["evaluation"]["qualityScore"] >= 75
    assert report["evaluation"]["structuralScore"] >= 75
    assert report["evaluation"]["coachUsefulnessScore"] >= 75
    assert report["evaluation"]["passed"] is True
    check_ids = {check["id"] for check in report["evaluation"]["checks"]}
    assert "retrieval_explainability_present" in check_ids
    assert "knowledge_event_type_coverage" in check_ids
    assert {
        "suggestion_specificity",
        "target_measurability",
        "route_context_relevance",
        "no_overclaim_score",
        "coach_usefulness_score",
    }.issubset(check_ids)
    dimension_ids = {dimension["id"] for dimension in report["evaluation"]["qualityDimensions"]}
    assert {
        "suggestion_specificity",
        "target_measurability",
        "route_context_relevance",
        "no_overclaim_score",
        "coach_usefulness_score",
    }.issubset(dimension_ids)
    assert all(dimension["score"] >= 70 for dimension in report["evaluation"]["qualityDimensions"])
    assert report["trace"]["traceId"] >= 1

    traces_response = client.get("/api/agent-traces/recent?limit=1")
    assert traces_response.status_code == 200
    traces = traces_response.json()
    assert len(traces) == 1
    assert traces[0]["traceId"] == report["trace"]["traceId"]
    assert traces[0]["workflowEngine"] in {"langgraph", "python_node_runner"}
    assert traces[0]["qualityScore"] == report["evaluation"]["qualityScore"]


def test_analyse_session_route_simulation_returns_sample_trip_contract() -> None:
    response = client.post(
        "/api/analyse-session",
        json={
            "mode": "route_simulation",
            "scenario": "route_grounded",
            "seed": 7201,
            "includeWearableData": True,
        },
    )

    assert response.status_code == 200
    trip = response.json()
    assert trip["provenance"]["dataSource"] == "route_grounded_synthetic"
    assert trip["provenance"]["notRealDriverData"] is True
    assert trip["route"]["routeSource"] == "cached_osm_osrm_grounded_geometry"
    assert trip["route"]["routeGeometry"]
    assert len(trip["samples"]) > 100
    assert "lat" in trip["samples"][0]
    assert "lon" in trip["samples"][0]
    assert "heartRate" in trip["samples"][0]
    assert trip["metrics"]["riskEventCount"] == len(trip["events"])


def test_analyse_session_accepts_telemetry_json() -> None:
    samples = [
        {
            "timestamp": index,
            "speed": 8 + index * 0.2,
            "ax": -3.4 if index == 8 else 0.1,
            "ay": 0.2,
            "yaw_rate": 0.02,
        }
        for index in range(20)
    ]

    response = client.post(
        "/api/analyse-session",
        json={"mode": "telemetry_json", "samples": samples, "scenario": "json_test"},
    )

    assert response.status_code == 200
    trip = response.json()
    assert trip["provenance"]["dataSource"] == "telemetry_json"
    assert trip["samples"][0]["yawRate"] == 0.02
    assert trip["route"]["origin"] == "Cranfield University"
    assert trip["metrics"]["riskEventCount"] == len(trip["events"])


def test_analyse_session_accepts_csv_path(tmp_path) -> None:
    csv_path = Path(".pytest_tmp") / "vehicle_ingestion_test.csv"
    csv_path.parent.mkdir(exist_ok=True)
    csv_path.write_text(
        "timestamp,speed,ax,ay,yaw_rate\n"
        "0,4,0.1,0.1,0.01\n"
        "1,5,0.2,0.1,0.01\n"
        "2,6,-3.5,0.2,0.02\n"
        "3,5,-0.4,0.2,0.02\n",
        encoding="utf-8",
    )

    response = client.post(
        "/api/analyse-session",
        json={"mode": "csv_path", "vehicleCsvPath": str(csv_path), "scenario": "csv_test"},
    )

    assert response.status_code == 200
    trip = response.json()
    assert trip["provenance"]["dataSource"] == "csv_path"
    assert len(trip["samples"]) == 4
    assert trip["metrics"]["riskEventCount"] == len(trip["events"])


def test_conditional_report_revision_repairs_invalid_report() -> None:
    state: CoachAgentState = {
        "trip": {"id": "test-trip"},
        "route_context": {"name": "Test route", "origin": "Cranfield University", "destination": "Milton Keynes Midsummer Place"},
        "metrics": {"overallDrivingScore": 70, "overallSmoothnessScore": 70, "contextAdaptationScore": 80, "riskEventCount": 1},
        "events": [
            {
                "id": "event-1",
                "type": "harsh_braking",
                "severity": "medium",
                "segmentName": "North Crawley approach",
            }
        ],
        "retrieved_knowledge": [{"id": "braking_smoothness", "title": "Braking smoothness", "source": "test"}],
        "report": {"summary": "Stress detected."},
        "workflow_engine": "test",
        "workflow_nodes": [],
    }

    validated = validate_report_node(state)
    assert should_revise_report(validated) == "revise"

    revised = revise_report_node(validated)
    revalidated = validate_report_node(revised)

    assert should_revise_report(revalidated) == "return"
    assert revalidated["report_validation"]["passed"] is True
    assert revalidated["report"]["revisionApplied"] is True
    assert revalidated["report"]["revisionCount"] == 1
    assert "Stress detected" not in str(revalidated["report"])


def test_coach_chat_endpoint_returns_evidence_grounded_response(monkeypatch) -> None:
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr("backend.agent.coach_chat.is_deepseek_configured", lambda: False)

    session_response = client.post("/api/demo-session", json={"scenario": "high_lateral_acceleration"})
    assert session_response.status_code == 200
    trip = session_response.json()

    response = client.post(
        "/api/coach-chat",
        json={
            "trip": trip,
            "messages": [{"role": "user", "content": "Why was this event risky?"}],
            "selectedEvent": trip["events"][0],
        },
    )

    assert response.status_code == 200
    chat = response.json()
    assert chat["agentMode"] == "deterministic_chat_no_llm"
    assert chat["answer"]
    assert chat["evidenceUsed"]
    assert chat["coachingActions"]
    assert chat["followUpQuestions"]
    assert chat["retrievedKnowledge"]
    assert any(knowledge["source"] for knowledge in chat["retrievedKnowledge"])
    assert all(knowledge["matchedBy"] for knowledge in chat["retrievedKnowledge"])
    assert all(knowledge["whyUsed"] for knowledge in chat["retrievedKnowledge"])
    assert all(knowledge["retrievalMode"] == "rag_lite_explainable" for knowledge in chat["retrievedKnowledge"])
    assert any(evidence["type"] == "knowledge" for evidence in chat["evidenceUsed"])


def test_coaching_targets_endpoint_returns_measurable_next_drive_targets(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("backend.services.session_memory_service.DB_PATH", tmp_path / "session_memory.sqlite")

    baseline_response = client.post("/api/demo-session", json={"scenario": "smooth_baseline"})
    session_response = client.post("/api/demo-session", json={"scenario": "harsh_braking"})
    assert baseline_response.status_code == 200
    assert session_response.status_code == 200

    save_response = client.post("/api/session-memory/save", json={"trip": baseline_response.json(), "save": True})
    assert save_response.status_code == 200

    response = client.post("/api/coaching-targets", json={"trip": session_response.json(), "includeHistory": True})

    assert response.status_code == 200
    targets_response = response.json()
    assert targets_response["agentMode"] == "deterministic_coaching_targets"
    assert targets_response["hasHistory"] is True
    assert targets_response["previousSessionId"] == baseline_response.json()["id"]
    assert "deterministic metrics" in targets_response["evidencePolicy"]
    assert 1 <= len(targets_response["targets"]) <= 3

    target_ids = {target["id"] for target in targets_response["targets"]}
    assert "reduce-late-braking" in target_ids
    assert all(target["measurement"] for target in targets_response["targets"])
    assert all(target["whyItMatters"] for target in targets_response["targets"])
    assert all(target["nextAction"] for target in targets_response["targets"])
    assert all(target["evidence"] for target in targets_response["targets"])
    assert all(target["status"] == "active" for target in targets_response["targets"])


def test_target_completion_endpoint_tracks_previous_targets(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("backend.services.session_memory_service.DB_PATH", tmp_path / "session_memory.sqlite")

    previous_response = client.post("/api/demo-session", json={"scenario": "harsh_braking"})
    current_response = client.post("/api/demo-session", json={"scenario": "smooth_baseline"})
    assert previous_response.status_code == 200
    assert current_response.status_code == 200

    assert client.post("/api/session-memory/save", json={"trip": previous_response.json(), "save": True}).status_code == 200

    response = client.post("/api/target-completion", json={"trip": current_response.json()})

    assert response.status_code == 200
    completion = response.json()
    assert completion["agentMode"] == "deterministic_target_completion"
    assert completion["hasPreviousTargets"] is True
    assert completion["previousSessionId"] == previous_response.json()["id"]
    assert completion["totalPreviousTargets"] >= 1
    assert completion["results"]
    assert completion["activeTargets"]
    assert completion["policy"]
    assert any(result["targetId"] == "reduce-late-braking" for result in completion["results"])
    braking_result = next(result for result in completion["results"] if result["targetId"] == "reduce-late-braking")
    assert braking_result["completed"] is True
    assert braking_result["currentValue"] <= braking_result["targetValue"]


def test_memory_aware_coaching_endpoint_returns_history_summary(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("backend.services.session_memory_service.DB_PATH", tmp_path / "session_memory.sqlite")

    baseline_response = client.post("/api/demo-session", json={"scenario": "smooth_baseline"})
    previous_response = client.post("/api/demo-session", json={"scenario": "high_lateral_acceleration"})
    current_response = client.post("/api/demo-session", json={"scenario": "unstable_speed_control"})
    assert baseline_response.status_code == 200
    assert previous_response.status_code == 200
    assert current_response.status_code == 200

    assert client.post("/api/session-memory/save", json={"trip": baseline_response.json(), "save": True}).status_code == 200
    assert client.post("/api/session-memory/save", json={"trip": previous_response.json(), "save": True}).status_code == 200

    response = client.post(
        "/api/memory-aware-coaching",
        json={"trip": current_response.json(), "includeRecentSessions": 5},
    )

    assert response.status_code == 200
    memory = response.json()
    assert memory["agentMode"] == "deterministic_memory_aware_coaching"
    assert memory["hasMemory"] is True
    assert memory["previousSessionId"] == previous_response.json()["id"]
    assert memory["memorySummary"]
    assert memory["behaviourChangeSummary"]
    assert memory["repeatedPatterns"]
    assert memory["watchItems"]
    assert memory["evidence"]
    assert "does not create a driver diagnosis" in memory["memoryPolicy"]
    assert len(memory["scoreTrend"]) >= 3
    assert memory["scoreTrend"][-1]["isCurrent"] is True


def test_knowledge_evaluation_endpoint_returns_quality_checks() -> None:
    response = client.get("/api/knowledge/evaluation")

    assert response.status_code == 200
    evaluation = response.json()
    assert evaluation["knowledgeCount"] >= 8
    assert evaluation["qualityScore"] >= 85
    assert evaluation["passed"] is True
    check_ids = {check["id"] for check in evaluation["checks"]}
    assert {
        "unique_knowledge_ids",
        "schema_completeness",
        "source_provenance_present",
        "event_type_coverage",
        "retrieval_smoke_cases",
    }.issubset(check_ids)
    assert evaluation["eventTypeCoverage"]["missing"] == []
    assert all(case["hasEventMatch"] for case in evaluation["retrievalCases"])
    assert all(case["explainable"] for case in evaluation["retrievalCases"])


def test_session_memory_compares_and_saves_sessions(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("backend.services.session_memory_service.DB_PATH", tmp_path / "session_memory.sqlite")

    first_response = client.post("/api/demo-session", json={"scenario": "smooth_baseline"})
    second_response = client.post("/api/demo-session", json={"scenario": "agent_generated", "seed": 8888})
    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_compare = client.post("/api/session-memory/compare", json={"trip": first_response.json(), "save": True})
    assert first_compare.status_code == 200
    assert first_compare.json()["hasPrevious"] is False

    second_compare = client.post("/api/session-memory/compare", json={"trip": second_response.json(), "save": True})
    assert second_compare.status_code == 200
    comparison = second_compare.json()
    assert comparison["hasPrevious"] is True
    assert comparison["previousSessionId"] == first_response.json()["id"]
    assert comparison["insights"]
    assert "overallDrivingScore" in comparison["deltas"]
    assert comparison["recentSessions"]
