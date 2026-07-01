import type { RiskEvent, TripSample } from "@/types/driving";

type EventType = RiskEvent["type"];

type EventSpec = {
  type: EventType;
  evidenceKey: string;
  threshold: number;
  matches: (sample: TripSample, index: number, samples: TripSample[]) => boolean;
  magnitude: (segment: TripSample[], allSamples: TripSample[]) => number;
  explanation: (segment: TripSample[]) => string;
  suggestion: string;
};

function localSpeedRange(samples: TripSample[], index: number): number {
  const start = Math.max(0, index - 4);
  const end = Math.min(samples.length, index + 5);
  const window = samples.slice(start, end);
  const speeds = window.map((sample) => sample.speed);
  return Math.max(...speeds) - Math.min(...speeds);
}

function accelerationSignChanges(samples: TripSample[], index: number): number {
  const start = Math.max(0, index - 4);
  const end = Math.min(samples.length, index + 5);
  const ax = samples.slice(start, end).map((sample) => sample.ax);
  return ax
    .slice(1)
    .filter((value, i) => Math.sign(value) !== 0 && Math.sign(ax[i]) !== 0 && Math.sign(value) !== Math.sign(ax[i]))
    .length;
}

function severityFromRatio(ratio: number): RiskEvent["severity"] {
  if (ratio >= 1.55) return "high";
  if (ratio >= 1.2) return "medium";
  return "low";
}

function contextAdjustedSeverity(type: EventType, base: RiskEvent["severity"], segment: TripSample[], magnitude: number): RiskEvent["severity"] {
  const sample = segment[0];
  if (type === "late_braking_before_curve") {
    return magnitude > 3.4 ? "high" : "medium";
  }
  if (type === "high_speed_in_curve") {
    return magnitude > 4 ? "high" : "medium";
  }
  if (type === "high_lateral_acceleration") {
    if (sample.curvatureLevel === "low" && magnitude > 2.0) return "high";
    if (sample.curvatureLevel === "high" && magnitude < 2.45) return base === "high" ? "medium" : base;
  }
  if (type === "harsh_braking" && sample.roadContext === "urban_arrival" && magnitude < 3.6) {
    return "medium";
  }
  return base;
}

function segmentName(segment: TripSample[]): string {
  return segment[0]?.segmentName ?? "Route segment";
}

const eventSpecs: EventSpec[] = [
  {
    type: "late_braking_before_curve",
    evidenceKey: "peakDeceleration",
    threshold: 3.0,
    matches: (sample, index, samples) => {
      const nextSamples = samples.slice(index, Math.min(samples.length, index + 18));
      const approachingCurve = nextSamples.some((future) => future.roadContext === "country_curve");
      return sample.ax < -3.0 && (sample.roadContext === "village_approach" || sample.roadContext === "country_curve") && approachingCurve;
    },
    magnitude: (segment) => Math.max(...segment.map((sample) => Math.abs(sample.ax))),
    explanation: (segment) => `Late braking was detected before or at the beginning of ${segmentName(segment)}.`,
    suggestion: "Reduce speed earlier before similar country-road curves.",
  },
  {
    type: "high_speed_in_curve",
    evidenceKey: "speedAboveTarget",
    threshold: 2.5,
    matches: (sample) => sample.curvatureLevel === "high" && sample.speed - sample.targetSpeed > 2.5,
    magnitude: (segment) => Math.max(...segment.map((sample) => sample.speed - sample.targetSpeed)),
    explanation: (segment) => `Speed stayed above the route target through ${segmentName(segment)}.`,
    suggestion: "Settle speed before entering high-curvature sections.",
  },
  {
    type: "unstable_cornering",
    evidenceKey: "combinedCorneringDemand",
    threshold: 2.2,
    matches: (sample) => sample.curvatureLevel === "high" && Math.abs(sample.ay) > 1.75 && Math.abs(sample.yawRate) > 0.25,
    magnitude: (segment) => Math.max(...segment.map((sample) => Math.abs(sample.ay) + Math.abs(sample.yawRate) * 2)),
    explanation: (segment) => `Lateral acceleration and yaw rate rose together during ${segmentName(segment)}.`,
    suggestion: "Use a smoother steering arc and reduce entry speed before the bend.",
  },
  {
    type: "harsh_braking",
    evidenceKey: "peakDeceleration",
    threshold: 3.0,
    matches: (sample) => sample.ax < -3.0,
    magnitude: (segment) => Math.max(...segment.map((sample) => Math.abs(sample.ax))),
    explanation: (segment) => `A braking segment exceeded the harsh deceleration threshold in ${segmentName(segment)}.`,
    suggestion: "Brake earlier and more progressively before higher-demand segments.",
  },
  {
    type: "harsh_acceleration",
    evidenceKey: "peakAcceleration",
    threshold: 2.5,
    matches: (sample) => sample.ax > 2.5,
    magnitude: (segment) => Math.max(...segment.map((sample) => Math.abs(sample.ax))),
    explanation: (segment) => `Sharper throttle demand was detected in ${segmentName(segment)}.`,
    suggestion: "Apply throttle more progressively to improve comfort and energy efficiency.",
  },
  {
    type: "high_lateral_acceleration",
    evidenceKey: "peakLateralAcceleration",
    threshold: 2.0,
    matches: (sample) => Math.abs(sample.ay) > 2.0,
    magnitude: (segment) => Math.max(...segment.map((sample) => Math.abs(sample.ay))),
    explanation: (segment) => `Higher cornering demand was detected in ${segmentName(segment)}.`,
    suggestion: "Reduce entry speed before corners to improve stability.",
  },
  {
    type: "sharp_yaw_motion",
    evidenceKey: "peakYawRate",
    threshold: 0.35,
    matches: (sample) => Math.abs(sample.yawRate) > 0.35,
    magnitude: (segment) => Math.max(...segment.map((sample) => Math.abs(sample.yawRate))),
    explanation: (segment) => `Yaw rate indicates an abrupt heading change in ${segmentName(segment)}.`,
    suggestion: "Use smoother steering input and avoid abrupt corrections.",
  },
  {
    type: "unstable_speed_control",
    evidenceKey: "localSpeedRange",
    threshold: 4.0,
    matches: (sample, index, samples) =>
      sample.roadContext === "urban_arrival" && localSpeedRange(samples, index) > 4.0 && accelerationSignChanges(samples, index) >= 3,
    magnitude: (segment, allSamples) =>
      Math.max(...segment.map((sample) => localSpeedRange(allSamples, allSamples.findIndex((candidate) => candidate.timestamp === sample.timestamp)))),
    explanation: (segment) => `Stop-and-go speed variation was detected in ${segmentName(segment)}.`,
    suggestion: "Hold a steadier following gap and use smoother pedal transitions in urban traffic.",
  },
];

function buildEvent(spec: EventSpec, segment: TripSample[], allSamples: TripSample[], sequence: number): RiskEvent {
  const magnitude = spec.magnitude(segment, allSamples);
  const baseSeverity = severityFromRatio(magnitude / spec.threshold);
  const severity = contextAdjustedSeverity(spec.type, baseSeverity, segment, magnitude);
  const sample = segment[0];

  return {
    id: `${spec.type}-${sequence}`,
    type: spec.type,
    startTime: segment[0].timestamp,
    endTime: segment[segment.length - 1].timestamp,
    severity,
    roadContext: sample.roadContext,
    segmentName: sample.segmentName,
    contextualExplanation: spec.explanation(segment),
    shortExplanation: spec.explanation(segment),
    coachingSuggestion: spec.suggestion,
    evidence: {
      [spec.evidenceKey]: Number(magnitude.toFixed(2)),
      threshold: spec.threshold,
      targetSpeed: Number(sample.targetSpeed.toFixed(1)),
      speedLimit: Number(sample.speedLimit.toFixed(1)),
      roadContext: sample.roadContext,
      segmentName: sample.segmentName,
      sampleCount: segment.length,
    },
  };
}

function overlapsExisting(segment: TripSample[], events: RiskEvent[], type: EventType): boolean {
  if (type !== "harsh_braking" && type !== "high_lateral_acceleration" && type !== "sharp_yaw_motion") {
    return false;
  }
  return events.some((event) => {
    const equivalent =
      (type === "harsh_braking" && event.type === "late_braking_before_curve") ||
      (type === "high_lateral_acceleration" && event.type === "unstable_cornering") ||
      (type === "sharp_yaw_motion" && event.type === "unstable_cornering");
    return equivalent && segment[0].timestamp <= event.endTime && segment[segment.length - 1].timestamp >= event.startTime;
  });
}

function severityRank(severity: RiskEvent["severity"]): number {
  if (severity === "high") return 3;
  if (severity === "medium") return 2;
  return 1;
}

function dedupeEvents(events: RiskEvent[]): RiskEvent[] {
  const strongestByType = new Map<EventType, RiskEvent>();
  events.forEach((event) => {
    const current = strongestByType.get(event.type);
    if (!current || severityRank(event.severity) > severityRank(current.severity)) {
      strongestByType.set(event.type, event);
    }
  });
  return Array.from(strongestByType.values()).sort((a, b) => a.startTime - b.startTime);
}

export function detectRiskEvents(samples: TripSample[]): RiskEvent[] {
  const events: RiskEvent[] = [];

  eventSpecs.forEach((spec) => {
    let activeSegment: TripSample[] = [];

    samples.forEach((sample, index) => {
      if (spec.matches(sample, index, samples)) {
        activeSegment.push(sample);
        return;
      }

      if (activeSegment.length > 0) {
        if (!overlapsExisting(activeSegment, events, spec.type)) {
          events.push(buildEvent(spec, activeSegment, samples, events.length + 1));
        }
        activeSegment = [];
      }
    });

    if (activeSegment.length > 0 && !overlapsExisting(activeSegment, events, spec.type)) {
      events.push(buildEvent(spec, activeSegment, samples, events.length + 1));
    }
  });

  return dedupeEvents(events);
}
