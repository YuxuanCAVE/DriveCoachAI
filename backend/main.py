from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.agent.coach_chat import run_coach_chat
from backend.agent.coach_workflow import run_coach_workflow
from backend.evaluation.knowledge_evaluator import evaluate_knowledge_base
from backend.evaluation.trace_store import recent_agent_traces
from backend.ingestion.session_ingestion_service import IngestionError, analyse_session
from backend.schemas import (
    AnalyseSessionRequest,
    CoachChatRequest,
    CoachReportRequest,
    CoachingTargetsRequest,
    DemoSessionRequest,
    MemoryAwareCoachingRequest,
    SessionMemoryRequest,
    TargetCompletionRequest,
)
from backend.services.coaching_target_service import generate_coaching_targets
from backend.services.demo_session_service import generate_demo_session, list_scenarios
from backend.services.memory_aware_coaching_service import generate_memory_aware_coaching
from backend.services.session_memory_service import compare_and_optionally_save, recent_sessions, save_session
from backend.services.target_completion_service import evaluate_target_completion

app = FastAPI(
    title="DriveCoach AI Backend",
    description="Deterministic backend bridge for the DriveCoach AI post-drive coaching demo.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/scenarios")
def scenarios() -> list[dict]:
    return list_scenarios()


@app.post("/api/demo-session")
def demo_session(request: DemoSessionRequest) -> dict:
    return generate_demo_session(
        include_wearable_data=request.includeWearableData,
        seed=request.seed,
        scenario=request.scenario,
        duration_seconds=request.durationSeconds,
        sample_rate_hz=request.sampleRateHz,
    )


@app.post("/api/analyse-session")
def analyse_session_endpoint(request: AnalyseSessionRequest) -> dict:
    try:
        return analyse_session(request.model_dump())
    except IngestionError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/coach-report")
def coach_report(request: CoachReportRequest) -> dict:
    return run_coach_workflow(request.trip)


@app.post("/api/coaching-targets")
def coaching_targets(request: CoachingTargetsRequest) -> dict:
    return generate_coaching_targets(request.trip, include_history=request.includeHistory)


@app.post("/api/target-completion")
def target_completion(request: TargetCompletionRequest) -> dict:
    return evaluate_target_completion(request.trip)


@app.post("/api/memory-aware-coaching")
def memory_aware_coaching(request: MemoryAwareCoachingRequest) -> dict:
    return generate_memory_aware_coaching(request.trip, include_recent_sessions=request.includeRecentSessions)


@app.post("/api/coach-chat")
def coach_chat(request: CoachChatRequest) -> dict:
    return run_coach_chat(
        trip=request.trip,
        messages=[message.model_dump() for message in request.messages],
        selected_event=request.selectedEvent,
    )


@app.get("/api/agent-traces/recent")
def agent_traces_recent(limit: int = 10) -> list[dict]:
    return recent_agent_traces(limit=limit)


@app.get("/api/knowledge/evaluation")
def knowledge_evaluation() -> dict:
    return evaluate_knowledge_base()


@app.get("/api/session-memory/recent")
def session_memory_recent(limit: int = 8) -> list[dict]:
    return recent_sessions(limit=limit)


@app.post("/api/session-memory/save")
def session_memory_save(request: SessionMemoryRequest) -> dict:
    save_session(request.trip)
    return {"saved": True, "sessionId": request.trip.get("id")}


@app.post("/api/session-memory/compare")
def session_memory_compare(request: SessionMemoryRequest) -> dict:
    return compare_and_optionally_save(request.trip, save=request.save)
