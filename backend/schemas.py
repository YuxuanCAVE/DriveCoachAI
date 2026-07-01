from typing import Any, Literal

from pydantic import BaseModel, Field


ScenarioKey = Literal[
    "mixed_route_review",
    "agent_generated",
    "smooth_baseline",
    "harsh_braking",
    "high_lateral_acceleration",
    "unstable_speed_control",
    "wearable_connected",
    "wearable_not_connected",
]


class DemoSessionRequest(BaseModel):
    scenario: ScenarioKey = "mixed_route_review"
    includeWearableData: bool = False
    seed: int | None = Field(default=None, ge=0)
    durationSeconds: int | None = Field(default=None, ge=60)
    sampleRateHz: int = Field(default=1, ge=1, le=10)


class CoachReportRequest(BaseModel):
    trip: dict[str, Any]


class CoachingTargetsRequest(BaseModel):
    trip: dict[str, Any]
    includeHistory: bool = True


class TargetCompletionRequest(BaseModel):
    trip: dict[str, Any]


class MemoryAwareCoachingRequest(BaseModel):
    trip: dict[str, Any]
    includeRecentSessions: int = Field(default=5, ge=2, le=8)


class AnalyseSessionRequest(BaseModel):
    mode: Literal["telemetry_json", "csv_path", "route_simulation"]
    samples: list[dict[str, Any]] | None = None
    vehicleCsvPath: str | None = None
    origin: str | None = "Cranfield University"
    destination: str | None = "Milton Keynes Midsummer Place"
    scenario: str | None = "route_grounded"
    includeWearableData: bool = False
    seed: int | None = Field(default=None, ge=0)
    durationSeconds: int | None = Field(default=None, ge=60)
    sampleRateHz: int = Field(default=1, ge=1, le=10)


class SessionMemoryRequest(BaseModel):
    trip: dict[str, Any]
    save: bool = True


class CoachChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class CoachChatRequest(BaseModel):
    trip: dict[str, Any]
    messages: list[CoachChatMessage] = Field(min_length=1, max_length=20)
    selectedEvent: dict[str, Any] | None = None
