import type { MemoryAwareCoachingResponse, SampleTrip } from "@/types/driving";

export function generateLocalMemoryAwareFallback(trip: SampleTrip): MemoryAwareCoachingResponse {
  return {
    generatedAt: new Date().toISOString(),
    sessionId: trip.id,
    agentMode: "frontend_local_memory_fallback",
    hasMemory: false,
    previousSessionId: null,
    memorySummary: "No previous backend memory is available in this view. This session can act as the baseline for future comparison.",
    behaviourChangeSummary: "There is not enough stored history yet to describe a driving-behaviour trend.",
    improvements: ["No historical improvement signal is available yet."],
    repeatedPatterns: ["No repeated pattern is established yet; keep collecting comparable route reviews."],
    watchItems: ["Use the next generated session to compare score movement, risk-event count, and route-context patterns."],
    scoreTrend: [
      {
        sessionId: trip.id,
        label: trip.route.name,
        storedAt: trip.createdAt,
        overallScore: trip.metrics.overallDrivingScore,
        longitudinalScore: trip.metrics.longitudinalSmoothnessScore,
        lateralScore: trip.metrics.lateralStabilityScore,
        riskEventCount: trip.metrics.riskEventCount,
        isCurrent: true,
      },
    ],
    recentSessions: [],
    evidence: [
      `Current session: ${trip.id}`,
      `Current score: ${Math.round(trip.metrics.overallDrivingScore)}/100`,
      `Current risk events: ${trip.metrics.riskEventCount}`,
    ],
    memoryPolicy:
      "DriveCoach uses recent session memory only to compare measurable driving patterns. It does not create a driver diagnosis, medical inference, or long-term behavioural label.",
  };
}
