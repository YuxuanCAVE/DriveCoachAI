import type {
  CoachChatMessage,
  CoachChatResponse,
  CoachReport,
  CoachingTargetsResponse,
  MemoryAwareCoachingResponse,
  RiskEvent,
  SampleTrip,
  SessionComparison,
  TargetCompletionResponse,
} from "@/types/driving";

const API_BASE_URL = process.env.NEXT_PUBLIC_DRIVECOACH_API_BASE_URL ?? "http://127.0.0.1:8000";

export type ScenarioKey =
  | "agent_generated"
  | "mixed_route_review"
  | "smooth_baseline"
  | "harsh_braking"
  | "high_lateral_acceleration"
  | "unstable_speed_control"
  | "wearable_connected"
  | "wearable_not_connected";

type DemoSessionOptions = {
  scenario: ScenarioKey;
  includeWearableData: boolean;
  seed: number;
  signal?: AbortSignal;
};

export async function fetchDemoSession({ scenario, includeWearableData, seed, signal }: DemoSessionOptions): Promise<SampleTrip> {
  const response = await fetch(`${API_BASE_URL}/api/demo-session`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      scenario,
      includeWearableData,
      seed,
    }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Demo session API failed with status ${response.status}`);
  }

  return response.json() as Promise<SampleTrip>;
}

export async function fetchCoachReport(trip: SampleTrip, signal?: AbortSignal): Promise<CoachReport> {
  const response = await fetch(`${API_BASE_URL}/api/coach-report`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ trip }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Coach report API failed with status ${response.status}`);
  }

  return response.json() as Promise<CoachReport>;
}

export async function fetchCoachChat({
  trip,
  messages,
  selectedEvent,
  signal,
}: {
  trip: SampleTrip;
  messages: CoachChatMessage[];
  selectedEvent?: RiskEvent;
  signal?: AbortSignal;
}): Promise<CoachChatResponse> {
  const response = await fetch(`${API_BASE_URL}/api/coach-chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      trip,
      messages,
      selectedEvent,
    }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Coach chat API failed with status ${response.status}`);
  }

  return response.json() as Promise<CoachChatResponse>;
}

export async function fetchCoachingTargets(
  trip: SampleTrip,
  includeHistory = true,
  signal?: AbortSignal,
): Promise<CoachingTargetsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/coaching-targets`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ trip, includeHistory }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Coaching targets API failed with status ${response.status}`);
  }

  return response.json() as Promise<CoachingTargetsResponse>;
}

export async function fetchMemoryAwareCoaching(
  trip: SampleTrip,
  includeRecentSessions = 5,
  signal?: AbortSignal,
): Promise<MemoryAwareCoachingResponse> {
  const response = await fetch(`${API_BASE_URL}/api/memory-aware-coaching`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ trip, includeRecentSessions }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Memory-aware coaching API failed with status ${response.status}`);
  }

  return response.json() as Promise<MemoryAwareCoachingResponse>;
}

export async function fetchTargetCompletion(trip: SampleTrip, signal?: AbortSignal): Promise<TargetCompletionResponse> {
  const response = await fetch(`${API_BASE_URL}/api/target-completion`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ trip }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Target completion API failed with status ${response.status}`);
  }

  return response.json() as Promise<TargetCompletionResponse>;
}

export async function compareAndSaveSession(trip: SampleTrip, signal?: AbortSignal): Promise<SessionComparison> {
  const response = await fetch(`${API_BASE_URL}/api/session-memory/compare`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ trip, save: true }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`Session comparison API failed with status ${response.status}`);
  }

  return response.json() as Promise<SessionComparison>;
}
