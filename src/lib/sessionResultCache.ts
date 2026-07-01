import type { CoachReport, CoachingTargetsResponse, MemoryAwareCoachingResponse, TargetCompletionResponse } from "@/types/driving";

export type CachedResultSource = "backend" | "fallback";

export const coachReportCache = new Map<
  string,
  {
    report: CoachReport;
    source: CachedResultSource;
  }
>();

export const coachingTargetsCache = new Map<
  string,
  {
    targets: CoachingTargetsResponse;
    source: CachedResultSource;
  }
>();

export const memoryAwareCache = new Map<
  string,
  {
    memory: MemoryAwareCoachingResponse;
    source: CachedResultSource;
  }
>();

export const targetCompletionCache = new Map<
  string,
  {
    completion: TargetCompletionResponse;
    source: CachedResultSource;
  }
>();
