export type RoadContext =
  | "campus_exit"
  | "rural_straight"
  | "village_approach"
  | "country_curve"
  | "arterial_cruise"
  | "roundabout_or_junction"
  | "urban_arrival"
  | "destination";

export type RoadSegment = {
  id: string;
  name: string;
  startTime: number;
  endTime: number;
  context: RoadContext;
  speedLimit: number;
  targetSpeed: number;
  curvatureLevel: "low" | "medium" | "high";
  trafficComplexity: "low" | "medium" | "high";
  expectedLateralDemand: "low" | "medium" | "high";
  description: string;
};

export type RoutePreset = {
  id: string;
  name: string;
  origin: string;
  destination: string;
  distanceMiles: number;
  durationMinutes: number;
  routeSummary: string;
  waypoints: {
    label: string;
    x: number;
    y: number;
  }[];
  routeSource?: string;
  distanceMeters?: number;
  routeGeometry?: {
    label: string;
    lat: number;
    lon: number;
    context?: RoadContext | string;
  }[];
  curvatureProfile?: {
    label: string;
    lat: number;
    lon: number;
    context?: RoadContext | string;
    curvature: number;
  }[];
  segments: RoadSegment[];
};

export const cranfieldToMiltonKeynesRoute: RoutePreset = {
  id: "cranfield_to_milton_keynes",
  name: "Cranfield to Milton Keynes Midsummer Place",
  origin: "Cranfield University",
  destination: "Milton Keynes Midsummer Place",
  distanceMiles: 7.3,
  durationMinutes: 15,
  routeSummary:
    "A mixed rural-to-urban route with campus exit, country roads, curves, junctions, and urban arrival.",
  waypoints: [
    { label: "Cranfield", x: 0.1, y: 0.72 },
    { label: "North Crawley", x: 0.35, y: 0.38 },
    { label: "Broughton", x: 0.64, y: 0.55 },
    { label: "Milton Keynes", x: 0.88, y: 0.2 },
  ],
  segments: [
    {
      id: "campus_exit",
      name: "Cranfield campus / College Road exit",
      startTime: 0,
      endTime: 60,
      context: "campus_exit",
      speedLimit: 9,
      targetSpeed: 7,
      curvatureLevel: "low",
      trafficComplexity: "low",
      expectedLateralDemand: "low",
      description: "Low-speed departure from Cranfield University toward College Road and the airport edge.",
    },
    {
      id: "rural_straight",
      name: "North Crawley Road rural straight",
      startTime: 60,
      endTime: 180,
      context: "rural_straight",
      speedLimit: 22,
      targetSpeed: 20,
      curvatureLevel: "low",
      trafficComplexity: "low",
      expectedLateralDemand: "low",
      description: "Stable rural section toward North Crawley with higher target speed and low lateral demand.",
    },
    {
      id: "village_approach",
      name: "North Crawley village approach",
      startTime: 180,
      endTime: 240,
      context: "village_approach",
      speedLimit: 13,
      targetSpeed: 10,
      curvatureLevel: "medium",
      trafficComplexity: "medium",
      expectedLateralDemand: "medium",
      description: "Speed reduction toward the North Crawley village edge and tighter local-road context.",
    },
    {
      id: "country_curve",
      name: "Newport Road rural bend",
      startTime: 240,
      endTime: 330,
      context: "country_curve",
      speedLimit: 17,
      targetSpeed: 13,
      curvatureLevel: "high",
      trafficComplexity: "medium",
      expectedLateralDemand: "high",
      description: "Curving Newport Road rural section where speed choice affects lateral stability.",
    },
    {
      id: "arterial_cruise",
      name: "Broughton / Willen approach",
      startTime: 330,
      endTime: 480,
      context: "arterial_cruise",
      speedLimit: 20,
      targetSpeed: 18,
      curvatureLevel: "low",
      trafficComplexity: "medium",
      expectedLateralDemand: "low",
      description: "More stable section approaching Broughton and Willen on the Milton Keynes edge.",
    },
    {
      id: "roundabout_or_junction",
      name: "A422 / Monks Way junction",
      startTime: 480,
      endTime: 560,
      context: "roundabout_or_junction",
      speedLimit: 12,
      targetSpeed: 8,
      curvatureLevel: "high",
      trafficComplexity: "high",
      expectedLateralDemand: "high",
      description: "Braking, steering, and yaw-rate changes around the A422 / Monks Way junction context.",
    },
    {
      id: "urban_arrival",
      name: "Milton Keynes grid-road arrival",
      startTime: 560,
      endTime: 720,
      context: "urban_arrival",
      speedLimit: 13,
      targetSpeed: 8,
      curvatureLevel: "medium",
      trafficComplexity: "high",
      expectedLateralDemand: "medium",
      description: "Lower-speed stop-and-go traffic on the Milton Keynes grid-road arrival.",
    },
    {
      id: "destination",
      name: "Midsummer Place arrival",
      startTime: 720,
      endTime: 880,
      context: "destination",
      speedLimit: 8,
      targetSpeed: 2,
      curvatureLevel: "low",
      trafficComplexity: "medium",
      expectedLateralDemand: "low",
      description: "Final deceleration and arrival around Milton Keynes Midsummer Place.",
    },
  ],
};
