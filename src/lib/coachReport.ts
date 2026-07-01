import type { CoachReport, SampleTrip } from "@/types/driving";

export function generateMockCoachReport(trip: SampleTrip): CoachReport {
  const { metrics, events, route } = trip;
  const mainEvent = events[0];
  const hasLateBraking = events.some((event) => event.type === "late_braking_before_curve" || event.type === "harsh_braking");
  const hasHighLateral = events.some((event) => event.type === "high_lateral_acceleration" || event.type === "unstable_cornering");
  const hasHighSpeedCurve = events.some((event) => event.type === "high_speed_in_curve");
  const hasUrbanInstability = events.some((event) => event.type === "unstable_speed_control");

  const summary =
    metrics.overallDrivingScore >= 82
      ? `Your ${route.name} review shows generally smooth control across the mixed rural-to-urban route, with a few context-specific moments worth reviewing.`
      : `Your ${route.name} review shows the main improvement opportunity around route context: speed choice before the country-road curve and control smoothness through higher-demand segments.`;

  const keyFindings = [
    `Overall driving score was ${Math.round(metrics.overallDrivingScore)}/100, including a ${Math.round(metrics.contextAdaptationScore)}/100 context adaptation score.`,
    `${metrics.riskEventCount} context-aware risk events were detected across ${route.distanceMiles} miles.`,
    `The route moved from ${route.origin} through rural roads and junctions toward ${route.destination}.`,
  ];

  if (mainEvent) {
    keyFindings.push(`Main event: ${mainEvent.type.replaceAll("_", " ")} in ${mainEvent.segmentName}.`);
  }
  if (hasHighSpeedCurve) {
    keyFindings.push("Speed remained above the route target during the high-curvature country-road segment.");
  }

  const behaviourInsight = [
    "Your driving was generally smooth on the rural straight and arterial cruise sections.",
    hasLateBraking
      ? "The main improvement opportunity occurred before the country-road curve, where braking happened relatively late."
      : "Braking before the country-road curve was broadly progressive.",
    hasHighLateral
      ? "That was followed by higher lateral demand, so reducing speed earlier before similar curves would improve stability."
      : "Lateral control stayed within the expected range for most route segments.",
    hasUrbanInstability
      ? "The urban arrival also showed stop-and-go variation, which is useful to review separately from open-road behaviour."
      : "",
  ]
    .filter(Boolean)
    .join(" ");

  const driverStateInsight = metrics.wearableConnected
    ? `Optional wearable context was connected. Mean heart rate was ${metrics.meanHeartRate?.toFixed(0)} bpm, about ${metrics.heartRateDeltaPercent?.toFixed(1)}% from baseline. Treat this only as driver-state context for the route review, not as a medical assessment.`
    : "Wearable data is not connected. This route review is based on connected-vehicle telemetry only.";

  const nextSessionFocus = [
    hasLateBraking
      ? "On similar country-road curves, begin reducing speed earlier and make braking more progressive."
      : "Keep the current progressive braking pattern before curves and junctions.",
    hasHighLateral
      ? "Aim for a lower, steadier entry speed before high-curvature rural sections."
      : "Maintain smooth steering through medium and high-curvature sections.",
    "Compare rural straight, curve, junction, and urban-arrival segments separately rather than treating the trip as one generic drive.",
  ];

  return {
    summary,
    structuredSummary: {
      overallAssessment: summary,
      mainBehaviouralPattern: hasLateBraking
        ? "The dominant pattern is late speed reduction before higher-demand route sections."
        : hasHighLateral
          ? "The dominant pattern is elevated cornering demand linked to entry speed and steering smoothness."
          : hasUrbanInstability
            ? "The dominant pattern is speed fluctuation during the urban arrival section."
            : "The session shows generally smooth control with no dominant risk pattern.",
      routeContextExplanation: `This review is route-aware: the session runs from ${route.origin} to ${route.destination}, moving through rural roads, bends, junction context, and urban arrival.`,
      whyItMatters:
        "This matters because smoother speed choice, braking, and steering inputs improve comfort, stability, and predictability without making medical or fatigue claims.",
      nextDriveFocus: nextSessionFocus.slice(0, 3),
    },
    keyFindings,
    behaviourInsight,
    driverStateInsight,
    nextSessionFocus,
  };
}
