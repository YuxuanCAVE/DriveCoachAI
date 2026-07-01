import type { SampleTrip, TargetCompletionResponse } from "@/types/driving";

export function generateLocalTargetCompletionFallback(trip: SampleTrip): TargetCompletionResponse {
  return {
    generatedAt: new Date().toISOString(),
    sessionId: trip.id,
    agentMode: "frontend_local_target_completion_fallback",
    hasPreviousTargets: false,
    previousSessionId: null,
    summary: "No previous target set is available in the local fallback. This session creates the next measurable target baseline.",
    completionRate: 0,
    completedCount: 0,
    totalPreviousTargets: 0,
    results: [],
    completedTargets: [],
    continuingFocus: [],
    newlyGeneratedTargets: [],
    activeTargets: [],
    policy: "Target completion is calculated from previous targets and current telemetry metrics when backend memory is available.",
  };
}
