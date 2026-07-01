import type { RoadContext, RoutePreset } from "@/lib/routePresets";

export type TripSample = {
  timestamp: number;
  speed: number;
  ax: number;
  ay: number;
  yawRate: number;
  steeringAngle?: number;
  brake?: number;
  throttle?: number;
  roadContext: RoadContext;
  segmentId: string;
  segmentName: string;
  speedLimit: number;
  targetSpeed: number;
  curvatureLevel: "low" | "medium" | "high";
  trafficComplexity: "low" | "medium" | "high";
  expectedLateralDemand: "low" | "medium" | "high";
  distanceAlongRoute?: number;
  lat?: number;
  lon?: number;
  heartRate?: number;
};

export type RiskEvent = {
  id: string;
  type:
    | "harsh_braking"
    | "harsh_acceleration"
    | "high_lateral_acceleration"
    | "sharp_yaw_motion"
    | "unstable_speed_control"
    | "late_braking_before_curve"
    | "high_speed_in_curve"
    | "unstable_cornering";
  startTime: number;
  endTime: number;
  severity: "low" | "medium" | "high";
  evidence: Record<string, number | string>;
  roadContext: RoadContext;
  segmentName: string;
  contextualExplanation: string;
  shortExplanation: string;
  coachingSuggestion: string;
};

export type DrivingMetrics = {
  durationSeconds: number;
  meanSpeed: number;
  maxSpeed: number;
  speedStd: number;
  meanAbsAx: number;
  maxAbsAx: number;
  meanAbsAy: number;
  maxAbsAy: number;
  accelerationRms: number;
  yawRateRms: number;
  overallDrivingScore: number;
  overallSmoothnessScore: number;
  longitudinalSmoothnessScore: number;
  lateralStabilityScore: number;
  contextAdaptationScore: number;
  eventSafetyScore: number;
  riskEventCount: number;
  wearableConnected: boolean;
  meanHeartRate?: number;
  maxHeartRate?: number;
  baselineHeartRate?: number;
  heartRateDeltaPercent?: number;
};

export type SampleTrip = {
  id: string;
  title: string;
  createdAt: string;
  provenance?: {
    dataSource: "route_grounded_synthetic" | "telemetry_json" | "csv_path" | string;
    routeSource?: string;
    seed?: number;
    notRealDriverData?: boolean;
    assumptions?: string[];
    vehicleCsvPath?: string;
  };
  route: RoutePreset;
  samples: TripSample[];
  events: RiskEvent[];
  metrics: DrivingMetrics;
};

export type CoachReport = {
  summary: string;
  structuredSummary?: {
    overallAssessment?: string;
    mainBehaviouralPattern?: string;
    routeContextExplanation?: string;
    whyItMatters?: string;
    nextDriveFocus?: string[];
  };
  keyFindings: string[];
  behaviourInsight: string;
  driverStateInsight?: string;
  nextSessionFocus: string[];
  eventSuggestions?: {
    eventId?: string;
    type?: string;
    segmentName?: string;
    severity?: RiskEvent["severity"];
    suggestion?: string;
  }[];
  evidenceUsed?: {
    type: "metric" | "event" | "route_segment" | "knowledge" | string;
    label: string;
    value?: string;
  }[];
  retrievedKnowledge?: {
    id: string;
    title: string;
    source?: string;
    confidence?: "low" | "medium" | "high" | string;
    matchedBy?: string[];
    whyUsed?: string;
    retrievalMode?: string;
  }[];
  agentMode?: string;
  workflowEngine?: "langgraph" | "python_node_runner" | string;
  workflowNodes?: string[];
  workflowFallbackReason?: string;
  reportValidation?: {
    passed: boolean;
    notes: string[];
    revisionCount: number;
  };
  revisionCount?: number;
  revisionApplied?: boolean;
  revisionReason?: string;
  evaluation?: {
    qualityScore: number;
    passed: boolean;
    durationMs?: number;
    blockingFailures?: string[];
    checks: {
      id: string;
      passed: boolean;
      detail: string;
      metadata?: Record<string, unknown>;
    }[];
  };
  trace?: {
    traceId?: number;
    createdAt?: string;
    sessionId?: string;
    qualityScore?: number;
    evaluationPassed?: boolean;
    recorded?: boolean;
    error?: string;
  };
  llmProvider?: string;
  llmModel?: string;
  evidencePolicy?: string;
  sessionId?: string;
  validationNotes?: string[];
};

export type CoachChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type CoachChatResponse = {
  answer: string;
  evidenceUsed: {
    type: "metric" | "event" | "route_segment" | "knowledge" | string;
    label: string;
    value?: string;
  }[];
  coachingActions: string[];
  confidence: "low" | "medium" | "high";
  safetyNotes: string[];
  followUpQuestions: string[];
  agentMode?: string;
  retrievedKnowledge?: {
    id: string;
    title: string;
    source?: string;
    confidence?: "low" | "medium" | "high" | string;
    matchedBy?: string[];
    whyUsed?: string;
    retrievalMode?: string;
  }[];
  llmFallbackReason?: string;
};

export type CoachingTarget = {
  id: string;
  title: string;
  category: "behaviour" | "route_context" | "measurable_score" | string;
  priority: "low" | "medium" | "high";
  baselineValue: number;
  targetValue: number;
  unit: string;
  measurement: string;
  whyItMatters: string;
  nextAction: string;
  evidence: string[];
  routeContext: string[];
  previousValue?: number | null;
  trendVsPrevious?: "improved" | "needs_attention" | "unchanged" | null;
  status: "active" | string;
};

export type CoachingTargetsResponse = {
  generatedAt: string;
  sessionId: string;
  agentMode: string;
  evidencePolicy: string;
  hasHistory: boolean;
  previousSessionId?: string | null;
  targets: CoachingTarget[];
};

export type TargetCompletionResult = {
  targetId: string;
  title: string;
  category: string;
  priority: "low" | "medium" | "high";
  unit: string;
  previousBaselineValue: number;
  targetValue: number;
  currentValue: number;
  progressDelta: number;
  completed: boolean;
  status: "completed" | "continue_focus";
  measurement: string;
  nextAction: string;
  evidence: string[];
  routeContext: string[];
};

export type TargetCompletionResponse = {
  generatedAt: string;
  sessionId: string;
  agentMode: string;
  hasPreviousTargets: boolean;
  previousSessionId?: string | null;
  summary: string;
  completionRate: number;
  completedCount: number;
  totalPreviousTargets: number;
  results: TargetCompletionResult[];
  completedTargets: TargetCompletionResult[];
  continuingFocus: CoachingTarget[];
  newlyGeneratedTargets: CoachingTarget[];
  activeTargets: CoachingTarget[];
  policy: string;
};

export type SessionHistoryRecord = {
  id: string;
  created_at: string;
  stored_at: string;
  scenario_key?: string;
  scenario_label?: string;
  seed?: number;
  overall_score?: number;
  longitudinal_score?: number;
  lateral_score?: number;
  context_score?: number;
  risk_event_count?: number;
  max_abs_ax?: number;
  max_abs_ay?: number;
};

export type ScoreTrendPoint = {
  sessionId: string;
  label: string;
  storedAt: string;
  overallScore?: number | null;
  longitudinalScore?: number | null;
  lateralScore?: number | null;
  riskEventCount?: number | null;
  isCurrent: boolean;
};

export type MemoryAwareCoachingResponse = {
  generatedAt: string;
  sessionId: string;
  agentMode: string;
  hasMemory: boolean;
  previousSessionId?: string | null;
  memorySummary: string;
  behaviourChangeSummary: string;
  improvements: string[];
  repeatedPatterns: string[];
  watchItems: string[];
  scoreTrend: ScoreTrendPoint[];
  recentSessions: SessionHistoryRecord[];
  evidence: string[];
  memoryPolicy: string;
};

export type SessionComparison = {
  hasPrevious: boolean;
  currentSessionId: string;
  previousSessionId?: string | null;
  previousScenario?: string;
  insights: string[];
  deltas: Record<
    string,
    {
      value: number | null;
      direction: "improved" | "declined" | "unchanged";
    }
  >;
  recentSessions?: SessionHistoryRecord[];
};
