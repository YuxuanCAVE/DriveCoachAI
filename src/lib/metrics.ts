import type { DrivingMetrics, RiskEvent, TripSample } from "@/types/driving";
import { clamp, mean, rms, standardDeviation } from "@/lib/math";

const severityPenalty = (events: RiskEvent[]): number =>
  events.reduce((sum, event) => {
    if (event.severity === "high") return sum + 8;
    if (event.severity === "medium") return sum + 4;
    return sum + 1.5;
  }, 0);

function baselineHeartRate(samples: TripSample[]): number | undefined {
  const heartRateSamples = samples.filter((sample) => typeof sample.heartRate === "number");
  if (heartRateSamples.length === 0) return undefined;

  const startTime = heartRateSamples[0].timestamp;
  const duration = heartRateSamples[heartRateSamples.length - 1].timestamp - startTime;
  const baselineWindow =
    duration >= 60
      ? heartRateSamples.filter((sample) => sample.timestamp <= startTime + 60)
      : heartRateSamples.slice(0, Math.max(1, Math.ceil(heartRateSamples.length * 0.2)));

  return mean(baselineWindow.map((sample) => sample.heartRate ?? 0));
}

function contextAdaptationScore(samples: TripSample[], events: RiskEvent[]): number {
  if (samples.length === 0) return 0;

  const speedTargetPenalty = mean(samples.map((sample) => Math.max(0, sample.speed - sample.targetSpeed) * 2.2));
  const lateralContextPenalty = mean(
    samples.map((sample) => {
      const allowance =
        sample.expectedLateralDemand === "high" ? 2.15 : sample.expectedLateralDemand === "medium" ? 1.45 : 0.8;
      return Math.max(0, Math.abs(sample.ay) - allowance) * 12;
    }),
  );
  const urbanInstabilityPenalty = mean(
    samples
      .filter((sample) => sample.roadContext === "urban_arrival")
      .map((sample) => Math.max(0, Math.abs(sample.ax) - 0.9) * 7),
  );

  const curveSamples = samples.filter((sample) => sample.roadContext === "country_curve");
  const curveEntry = curveSamples.slice(0, Math.min(18, curveSamples.length));
  const curveEntryPenalty = curveEntry.length
    ? mean(curveEntry.map((sample) => Math.max(0, sample.speed - sample.targetSpeed) * 4))
    : 0;
  const contextEventPenalty = events.filter((event) =>
    ["late_braking_before_curve", "high_speed_in_curve", "unstable_cornering"].includes(event.type),
  ).length * 4;

  // MVP heuristic only: these scores are research-informed product signals, not validated safety scores.
  return clamp(100 - speedTargetPenalty - lateralContextPenalty - urbanInstabilityPenalty - curveEntryPenalty - contextEventPenalty, 0, 100);
}

export function calculateDrivingMetrics(samples: TripSample[], events: RiskEvent[]): DrivingMetrics {
  const speeds = samples.map((sample) => sample.speed);
  const ax = samples.map((sample) => sample.ax);
  const ay = samples.map((sample) => sample.ay);
  const yawRates = samples.map((sample) => sample.yawRate);
  const durationSeconds = samples.length > 1 ? samples[samples.length - 1].timestamp - samples[0].timestamp : 0;

  const meanAbsAx = mean(ax.map(Math.abs));
  const maxAbsAx = Math.max(...ax.map(Math.abs));
  const meanAbsAy = mean(ay.map(Math.abs));
  const maxAbsAy = Math.max(...ay.map(Math.abs));
  const accelerationRms = rms(ax);
  const yawRateRms = rms(yawRates);
  const eventPenalty = severityPenalty(events);

  // MVP heuristic only: these scores are transparent review aids, not validated safety scores.
  const longitudinalSmoothnessScore = clamp(100 - meanAbsAx * 14 - maxAbsAx * 5.2 - eventPenalty * 0.35, 0, 100);
  const lateralStabilityScore = clamp(100 - meanAbsAy * 15 - maxAbsAy * 6.2 - yawRateRms * 32 - eventPenalty * 0.3, 0, 100);
  const eventSafetyScore = clamp(100 - eventPenalty, 0, 100);
  const contextScore = contextAdaptationScore(samples, events);
  const overallDrivingScore = clamp(
    0.35 * longitudinalSmoothnessScore +
      0.3 * lateralStabilityScore +
      0.2 * eventSafetyScore +
      0.15 * contextScore,
    0,
    100,
  );

  const wearableConnected = samples.some((sample) => typeof sample.heartRate === "number");
  const heartRates = samples
    .map((sample) => sample.heartRate)
    .filter((value): value is number => typeof value === "number");
  const baseline = baselineHeartRate(samples);
  const meanHeartRate = heartRates.length > 0 ? mean(heartRates) : undefined;

  return {
    durationSeconds,
    meanSpeed: mean(speeds),
    maxSpeed: Math.max(...speeds),
    speedStd: standardDeviation(speeds),
    meanAbsAx,
    maxAbsAx,
    meanAbsAy,
    maxAbsAy,
    accelerationRms,
    yawRateRms,
    overallDrivingScore,
    overallSmoothnessScore: overallDrivingScore,
    longitudinalSmoothnessScore,
    lateralStabilityScore,
    contextAdaptationScore: contextScore,
    eventSafetyScore,
    riskEventCount: events.length,
    wearableConnected,
    meanHeartRate,
    maxHeartRate: heartRates.length > 0 ? Math.max(...heartRates) : undefined,
    baselineHeartRate: baseline,
    heartRateDeltaPercent:
      baseline && meanHeartRate ? ((meanHeartRate - baseline) / baseline) * 100 : undefined,
  };
}
