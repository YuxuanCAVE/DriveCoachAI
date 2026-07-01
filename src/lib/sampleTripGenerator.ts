import type { RoadSegment, RoutePreset } from "@/lib/routePresets";
import { cranfieldToMiltonKeynesRoute } from "@/lib/routePresets";
import type { SampleTrip, TripSample } from "@/types/driving";
import { calculateDrivingMetrics } from "@/lib/metrics";
import { detectRiskEvents } from "@/lib/eventDetector";
import { clamp } from "@/lib/math";

type GenerateOptions = {
  durationSeconds?: number;
  sampleRateHz?: number;
  includeWearableData?: boolean;
  seed?: number;
  route?: RoutePreset;
};

function seededRandom(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (state * 1664525 + 1013904223) >>> 0;
    return state / 4294967296;
  };
}

function noise(random: () => number, amplitude: number): number {
  return (random() - 0.5) * 2 * amplitude;
}

function influence(timestamp: number, center: number, radius: number): number {
  const distance = Math.abs(timestamp - center);
  return distance > radius ? 0 : 1 - distance / radius;
}

function segmentAt(route: RoutePreset, timestamp: number): RoadSegment {
  return (
    route.segments.find((segment) => timestamp >= segment.startTime && timestamp <= segment.endTime) ??
    route.segments[route.segments.length - 1]
  );
}

function baseSpeed(segment: RoadSegment, progress: number): number {
  switch (segment.context) {
    case "campus_exit":
      return 1 + progress * 8.5;
    case "rural_straight":
      return segment.targetSpeed + Math.sin(progress * Math.PI * 2) * 0.7;
    case "village_approach":
      return 19 - progress * 9.5;
    case "country_curve":
      return 14.5 - Math.sin(progress * Math.PI) * 2.2;
    case "arterial_cruise":
      return segment.targetSpeed + Math.sin(progress * Math.PI * 3) * 0.55;
    case "roundabout_or_junction":
      return 15 - Math.sin(progress * Math.PI) * 8.5;
    case "urban_arrival":
      return 8.2 + Math.sin(progress * Math.PI * 8) * 1.2;
    case "destination":
      return Math.max(0, 7 - progress * 7.5);
  }
}

function distanceAlongRoute(route: RoutePreset, timestamp: number): number {
  const endTime = route.segments[route.segments.length - 1].endTime;
  return clamp(timestamp / endTime, 0, 1);
}

export function generateSampleTrip(options: GenerateOptions = {}): SampleTrip {
  const route = options.route ?? cranfieldToMiltonKeynesRoute;
  const sampleRateHz = options.sampleRateHz ?? 1;
  const includeWearableData = options.includeWearableData ?? false;
  const seed = options.seed ?? Date.now();
  const random = seededRandom(seed);
  const routeEndTime = route.segments[route.segments.length - 1].endTime;
  const durationSeconds = options.durationSeconds ?? routeEndTime;
  const interval = 1 / sampleRateHz;
  const sampleCount = Math.floor(durationSeconds * sampleRateHz) + 1;
  const hrBaseline = 72 + random() * 7;

  const lateBrakeCenter = 238;
  const curveDemandCenter = 276;
  const junctionAccelerationCenter = 548;
  const urbanFluctuationCenter = 630;

  const samples: TripSample[] = Array.from({ length: sampleCount }, (_, index) => {
    const timestamp = Number((index * interval).toFixed(2));
    const segment = segmentAt(route, timestamp);
    const segmentDuration = Math.max(1, segment.endTime - segment.startTime);
    const progress = clamp((timestamp - segment.startTime) / segmentDuration, 0, 1);

    const lateBrake = influence(timestamp, lateBrakeCenter, 8);
    const curveDemand = influence(timestamp, curveDemandCenter, 16);
    const junctionAcceleration = influence(timestamp, junctionAccelerationCenter, 7);
    const urbanFluctuation = influence(timestamp, urbanFluctuationCenter, 42);

    const contextNoise =
      segment.trafficComplexity === "high" ? 0.55 : segment.trafficComplexity === "medium" ? 0.32 : 0.18;
    const speed =
      baseSpeed(segment, progress) -
      lateBrake * 3.4 +
      junctionAcceleration * 2.8 +
      Math.sin(timestamp * 0.7) * urbanFluctuation * 2.0 +
      noise(random, contextNoise);

    const targetDelta = clamp(segment.targetSpeed - speed, -5, 5);
    const progressiveAx =
      targetDelta * 0.08 +
      (segment.context === "village_approach" ? -0.35 : 0) +
      (segment.context === "destination" ? -0.45 : 0) +
      noise(random, 0.14);
    const ax =
      progressiveAx -
      lateBrake * (3.05 + random() * 0.35) +
      junctionAcceleration * (2.55 + random() * 0.28) +
      Math.sin(timestamp * 1.65) * urbanFluctuation * 0.8;

    const curveAy =
      segment.curvatureLevel === "high"
        ? 0.85 + Math.sin(progress * Math.PI) * 0.95
        : segment.curvatureLevel === "medium"
          ? 0.35 + Math.sin(progress * Math.PI) * 0.35
          : 0.08;
    const ay =
      curveAy +
      curveDemand * (0.7 + speed / 38) +
      (segment.context === "roundabout_or_junction" ? Math.sin(progress * Math.PI) * 1.05 : 0) +
      Math.sin(timestamp * 1.4) * urbanFluctuation * 0.25 +
      noise(random, 0.12);

    const yawRate =
      (segment.curvatureLevel === "high" ? 0.13 : segment.curvatureLevel === "medium" ? 0.07 : 0.018) +
      curveDemand * 0.12 +
      (segment.context === "roundabout_or_junction" ? Math.sin(progress * Math.PI) * 0.26 : 0) +
      noise(random, 0.018);

    const brake = clamp(Math.max(0, -ax) * 0.16 + lateBrake * 0.8 + (segment.context === "destination" ? progress * 0.55 : 0), 0, 1);
    const throttle = clamp(Math.max(0, ax) * 0.18 + junctionAcceleration * 0.72 + (segment.context === "rural_straight" ? 0.25 : 0.12) + noise(random, 0.04), 0, 1);

    const dynamicActivation =
      lateBrake * 4.6 +
      curveDemand * 3.5 +
      junctionAcceleration * 2.8 +
      urbanFluctuation * 1.4 +
      (segment.trafficComplexity === "high" ? 1.2 : 0);
    const heartRate = includeWearableData
      ? hrBaseline + Math.sin(timestamp / 48) * 1.8 + dynamicActivation + noise(random, 0.9)
      : undefined;

    return {
      timestamp,
      speed: Number(clamp(speed, 0, segment.speedLimit + 4).toFixed(2)),
      ax: Number(ax.toFixed(2)),
      ay: Number(ay.toFixed(2)),
      yawRate: Number(yawRate.toFixed(3)),
      steeringAngle: Number((ay * 6.4 + yawRate * 22 + noise(random, 1.1)).toFixed(1)),
      brake: Number(brake.toFixed(2)),
      throttle: Number(throttle.toFixed(2)),
      roadContext: segment.context,
      segmentId: segment.id,
      segmentName: segment.name,
      speedLimit: segment.speedLimit,
      targetSpeed: segment.targetSpeed,
      curvatureLevel: segment.curvatureLevel,
      trafficComplexity: segment.trafficComplexity,
      expectedLateralDemand: segment.expectedLateralDemand,
      distanceAlongRoute: Number(distanceAlongRoute(route, timestamp).toFixed(4)),
      heartRate: heartRate === undefined ? undefined : Number(heartRate.toFixed(1)),
    };
  });

  const events = detectRiskEvents(samples);
  const metrics = calculateDrivingMetrics(samples, events);

  return {
    id: `cranfield-mk-${seed}`,
    title: "Generated Cranfield to Milton Keynes Midsummer Place route review",
    createdAt: new Date().toISOString(),
    route,
    samples,
    events,
    metrics,
  };
}
