from __future__ import annotations

from datetime import datetime, timezone
from math import pi, sin, sqrt
from statistics import mean
from typing import Any

from backend.ingestion.route_geometry import CRANFIELD_TO_MK_GEOMETRY, route_curvature_profile, route_distance_m


def clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)


def standard_deviation(values: list[float]) -> float:
    if not values:
        return 0.0
    avg = mean(values)
    return sqrt(mean([(value - avg) ** 2 for value in values]))


def rms(values: list[float]) -> float:
    return sqrt(mean([value**2 for value in values])) if values else 0.0


class SeededRandom:
    def __init__(self, seed: int) -> None:
        self.state = seed & 0xFFFFFFFF

    def __call__(self) -> float:
        self.state = (self.state * 1664525 + 1013904223) & 0xFFFFFFFF
        return self.state / 4294967296


def noise(random: SeededRandom, amplitude: float) -> float:
    return (random() - 0.5) * 2 * amplitude


def influence(timestamp: float, center: float, radius: float) -> float:
    distance = abs(timestamp - center)
    return 0.0 if distance > radius else 1 - distance / radius


ROUTE: dict[str, Any] = {
    "id": "cranfield_to_milton_keynes",
    "name": "Cranfield to Milton Keynes Midsummer Place",
    "origin": "Cranfield University",
    "destination": "Milton Keynes Midsummer Place",
    "distanceMiles": 7.3,
    "durationMinutes": 15,
    "routeSummary": "A mixed rural-to-urban route with campus exit, country roads, curves, junctions, and urban arrival.",
    "waypoints": [
        {"label": "Cranfield", "x": 0.1, "y": 0.72},
        {"label": "North Crawley", "x": 0.35, "y": 0.38},
        {"label": "Broughton", "x": 0.64, "y": 0.55},
        {"label": "Milton Keynes", "x": 0.88, "y": 0.2},
    ],
    "segments": [
        {
            "id": "campus_exit",
            "name": "Cranfield campus / College Road exit",
            "startTime": 0,
            "endTime": 60,
            "context": "campus_exit",
            "speedLimit": 9,
            "targetSpeed": 7,
            "curvatureLevel": "low",
            "trafficComplexity": "low",
            "expectedLateralDemand": "low",
            "description": "Low-speed departure from Cranfield University toward College Road and the airport edge.",
        },
        {
            "id": "rural_straight",
            "name": "North Crawley Road rural straight",
            "startTime": 60,
            "endTime": 180,
            "context": "rural_straight",
            "speedLimit": 22,
            "targetSpeed": 20,
            "curvatureLevel": "low",
            "trafficComplexity": "low",
            "expectedLateralDemand": "low",
            "description": "Stable rural section toward North Crawley with higher target speed and low lateral demand.",
        },
        {
            "id": "village_approach",
            "name": "North Crawley village approach",
            "startTime": 180,
            "endTime": 240,
            "context": "village_approach",
            "speedLimit": 13,
            "targetSpeed": 10,
            "curvatureLevel": "medium",
            "trafficComplexity": "medium",
            "expectedLateralDemand": "medium",
            "description": "Speed reduction toward the North Crawley village edge and tighter local-road context.",
        },
        {
            "id": "country_curve",
            "name": "Newport Road rural bend",
            "startTime": 240,
            "endTime": 330,
            "context": "country_curve",
            "speedLimit": 17,
            "targetSpeed": 13,
            "curvatureLevel": "high",
            "trafficComplexity": "medium",
            "expectedLateralDemand": "high",
            "description": "Curving Newport Road rural section where speed choice affects lateral stability.",
        },
        {
            "id": "arterial_cruise",
            "name": "Broughton / Willen approach",
            "startTime": 330,
            "endTime": 480,
            "context": "arterial_cruise",
            "speedLimit": 20,
            "targetSpeed": 18,
            "curvatureLevel": "low",
            "trafficComplexity": "medium",
            "expectedLateralDemand": "low",
            "description": "More stable section approaching Broughton and Willen on the Milton Keynes edge.",
        },
        {
            "id": "roundabout_or_junction",
            "name": "A422 / Monks Way junction",
            "startTime": 480,
            "endTime": 560,
            "context": "roundabout_or_junction",
            "speedLimit": 12,
            "targetSpeed": 8,
            "curvatureLevel": "high",
            "trafficComplexity": "high",
            "expectedLateralDemand": "high",
            "description": "Braking, steering, and yaw-rate changes around the A422 / Monks Way junction context.",
        },
        {
            "id": "urban_arrival",
            "name": "Milton Keynes grid-road arrival",
            "startTime": 560,
            "endTime": 720,
            "context": "urban_arrival",
            "speedLimit": 13,
            "targetSpeed": 8,
            "curvatureLevel": "medium",
            "trafficComplexity": "high",
            "expectedLateralDemand": "medium",
            "description": "Lower-speed stop-and-go traffic on the Milton Keynes grid-road arrival.",
        },
        {
            "id": "destination",
            "name": "Midsummer Place arrival",
            "startTime": 720,
            "endTime": 880,
            "context": "destination",
            "speedLimit": 8,
            "targetSpeed": 2,
            "curvatureLevel": "low",
            "trafficComplexity": "medium",
            "expectedLateralDemand": "low",
            "description": "Final deceleration and arrival around Milton Keynes Midsummer Place.",
        },
    ],
}


def route_with_geometry() -> dict[str, Any]:
    return {
        **ROUTE,
        "distanceMeters": round(route_distance_m()),
        "routeSource": "cached_osm_osrm_grounded_geometry",
        "routeGeometry": CRANFIELD_TO_MK_GEOMETRY,
        "curvatureProfile": route_curvature_profile(),
    }


SCENARIOS: dict[str, dict[str, Any]] = {
    "agent_generated": {
        "label": "AI-generated random demo",
        "seed": 9101,
        "defaultWearable": False,
        "description": "Seeded random route review for interactive demo sessions and memory comparison.",
        "expectedEvents": ["Generated dynamically from the selected seed"],
        "mapAnchors": ["Route-context hazards generated from the Cranfield to Milton Keynes route profile"],
        "profile": {},
    },
    "mixed_route_review": {
        "label": "Mixed route review",
        "seed": 1024,
        "defaultWearable": False,
        "description": "Balanced Cranfield to Milton Keynes review with several route-context risk moments.",
        "expectedEvents": [
            "late_braking_before_curve",
            "high_lateral_acceleration",
            "high_speed_in_curve",
            "unstable_cornering",
            "unstable_speed_control",
        ],
        "mapAnchors": [
            "North Crawley village approach before Newport Road rural bend",
            "A422 / Monks Way junction near the Milton Keynes edge",
            "Milton Keynes grid-road arrival toward Midsummer Place",
        ],
        "profile": {},
    },
    "smooth_baseline": {
        "label": "Smooth baseline",
        "seed": 3101,
        "defaultWearable": False,
        "description": "Reference drive with early speed settling and lower dynamic demand.",
        "expectedEvents": [],
        "mapAnchors": ["Full route used as a low-risk comparison baseline"],
        "profile": {
            "late_brake": 0.15,
            "curve_demand": 0.2,
            "junction_acceleration": 0.2,
            "urban_fluctuation": 0.18,
            "noise_scale": 0.45,
            "speed_bias": -0.9,
            "max_target_overspeed": 0.7,
            "ay_scale": 0.48,
            "yaw_rate_scale": 0.55,
            "dynamic_scale": 0.45,
        },
    },
    "harsh_braking": {
        "label": "Harsh braking",
        "seed": 3201,
        "defaultWearable": False,
        "description": "Late braking before a tighter rural segment approaching the Cranfield/Newport Road corridor.",
        "expectedEvents": [
            "late_braking_before_curve",
            "high_lateral_acceleration",
            "high_speed_in_curve",
            "unstable_cornering",
            "unstable_speed_control",
        ],
        "mapAnchors": ["North Crawley village approach", "Newport Road rural bend"],
        "profile": {
            "late_brake": 1.7,
            "curve_demand": 0.85,
            "junction_acceleration": 0.75,
            "urban_fluctuation": 0.75,
            "noise_scale": 0.9,
            "speed_bias": 0.25,
            "dynamic_scale": 1.15,
        },
    },
    "high_lateral_acceleration": {
        "label": "High lateral acceleration",
        "seed": 3301,
        "defaultWearable": False,
        "description": "Higher cornering demand on curving rural and junction sections.",
        "expectedEvents": ["high_lateral_acceleration", "unstable_cornering", "high_speed_in_curve"],
        "mapAnchors": ["North Crawley / Cranfield Road bend", "Newport Road rural bend", "A422 / Monks Way junction"],
        "profile": {
            "late_brake": 0.75,
            "curve_demand": 2.35,
            "junction_acceleration": 0.8,
            "urban_fluctuation": 0.65,
            "lateral_scale": 1.35,
            "yaw_scale": 1.35,
            "ay_scale": 1.35,
            "yaw_rate_scale": 1.35,
            "noise_scale": 0.8,
            "speed_bias": 0.85,
            "dynamic_scale": 1.2,
        },
    },
    "unstable_speed_control": {
        "label": "Unstable speed control",
        "seed": 3401,
        "defaultWearable": False,
        "description": "Stop-and-go speed variation around the urban arrival toward Midsummer Place.",
        "expectedEvents": [
            "high_lateral_acceleration",
            "high_speed_in_curve",
            "unstable_cornering",
            "unstable_speed_control",
            "harsh_acceleration",
            "harsh_braking",
        ],
        "mapAnchors": ["Broughton / Willen approach", "Milton Keynes grid-road arrival"],
        "profile": {
            "late_brake": 0.65,
            "curve_demand": 0.65,
            "junction_acceleration": 1.05,
            "urban_fluctuation": 2.3,
            "urban_ax_scale": 1.6,
            "noise_scale": 1.0,
            "speed_bias": 0.1,
            "dynamic_scale": 1.1,
        },
    },
    "wearable_connected": {
        "label": "Optional wearable connected",
        "seed": 3501,
        "defaultWearable": True,
        "description": "Standard route review with heart-rate context included as optional driver-state information.",
        "expectedEvents": [
            "late_braking_before_curve",
            "high_lateral_acceleration",
            "high_speed_in_curve",
            "unstable_cornering",
            "unstable_speed_control",
        ],
        "mapAnchors": ["Dynamic rural curve and junction sections"],
        "profile": {
            "late_brake": 1.0,
            "curve_demand": 1.0,
            "junction_acceleration": 1.0,
            "urban_fluctuation": 0.85,
            "noise_scale": 0.85,
            "dynamic_scale": 1.2,
        },
    },
    "wearable_not_connected": {
        "label": "Wearable not connected",
        "seed": 3601,
        "defaultWearable": False,
        "description": "Standard vehicle-only review with no heart-rate samples.",
        "expectedEvents": [
            "late_braking_before_curve",
            "high_lateral_acceleration",
            "high_speed_in_curve",
            "unstable_cornering",
        ],
        "mapAnchors": ["Vehicle telemetry only across the full route"],
        "profile": {
            "late_brake": 1.0,
            "curve_demand": 1.0,
            "junction_acceleration": 1.0,
            "urban_fluctuation": 0.85,
            "noise_scale": 0.85,
            "dynamic_scale": 1.0,
        },
    },
}


def generated_profile(seed: int) -> dict[str, Any]:
    random = SeededRandom(seed + 7919)
    scenario_blend = random()
    return {
        "late_brake": 0.25 + random() * (1.85 if scenario_blend > 0.25 else 0.55),
        "curve_demand": 0.25 + random() * (2.25 if scenario_blend > 0.15 else 0.65),
        "junction_acceleration": 0.25 + random() * 1.35,
        "urban_fluctuation": 0.25 + random() * (2.35 if scenario_blend > 0.45 else 0.85),
        "noise_scale": 0.55 + random() * 0.65,
        "speed_bias": -0.8 + random() * 1.8,
        "dynamic_scale": 0.75 + random() * 0.75,
        "ay_scale": 0.75 + random() * 0.7,
        "yaw_rate_scale": 0.8 + random() * 0.65,
        "urban_ax_scale": 0.8 + random() * 0.9,
    }


def scenario_config(scenario: str) -> dict[str, Any]:
    return SCENARIOS.get(scenario, SCENARIOS["mixed_route_review"])


def list_scenarios() -> list[dict[str, Any]]:
    return [
        {
            "key": key,
            "label": value["label"],
            "seed": value["seed"],
            "defaultWearable": value["defaultWearable"],
            "description": value["description"],
            "expectedEvents": value["expectedEvents"],
            "mapAnchors": value["mapAnchors"],
        }
        for key, value in SCENARIOS.items()
    ]


def segment_at(timestamp: float) -> dict[str, Any]:
    for segment in ROUTE["segments"]:
        if segment["startTime"] <= timestamp <= segment["endTime"]:
            return segment
    return ROUTE["segments"][-1]


def base_speed(segment: dict[str, Any], progress: float) -> float:
    context = segment["context"]
    if context == "campus_exit":
        return 1 + progress * 8.5
    if context == "rural_straight":
        return segment["targetSpeed"] + sin(progress * pi * 2) * 0.7
    if context == "village_approach":
        return 19 - progress * 9.5
    if context == "country_curve":
        return 14.5 - sin(progress * pi) * 2.2
    if context == "arterial_cruise":
        return segment["targetSpeed"] + sin(progress * pi * 3) * 0.55
    if context == "roundabout_or_junction":
        return 15 - sin(progress * pi) * 8.5
    if context == "urban_arrival":
        return 8.2 + sin(progress * pi * 8) * 1.2
    return max(0, 7 - progress * 7.5)


def route_progress(timestamp: float) -> float:
    return clamp(timestamp / ROUTE["segments"][-1]["endTime"], 0, 1)


def generate_samples(
    include_wearable_data: bool,
    seed: int,
    duration_seconds: int | None,
    sample_rate_hz: int,
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    random = SeededRandom(seed)
    route_end_time = ROUTE["segments"][-1]["endTime"]
    duration = duration_seconds or route_end_time
    interval = 1 / sample_rate_hz
    sample_count = int(duration * sample_rate_hz) + 1
    hr_baseline = 72 + random() * 7

    samples: list[dict[str, Any]] = []
    for index in range(sample_count):
        timestamp = round(index * interval, 2)
        segment = segment_at(timestamp)
        segment_duration = max(1, segment["endTime"] - segment["startTime"])
        progress = clamp((timestamp - segment["startTime"]) / segment_duration, 0, 1)

        late_brake = influence(timestamp, 238, 8) * profile.get("late_brake", 1.0)
        curve_demand = influence(timestamp, 276, 16) * profile.get("curve_demand", 1.0)
        junction_acceleration = influence(timestamp, 548, 7) * profile.get("junction_acceleration", 1.0)
        urban_fluctuation = influence(timestamp, 630, 42) * profile.get("urban_fluctuation", 1.0)

        context_noise = (0.55 if segment["trafficComplexity"] == "high" else 0.32 if segment["trafficComplexity"] == "medium" else 0.18) * profile.get("noise_scale", 1.0)
        speed = (
            base_speed(segment, progress)
            + profile.get("speed_bias", 0.0)
            - late_brake * 3.4
            + junction_acceleration * 2.8
            + sin(timestamp * 0.7) * urban_fluctuation * 2.0
            + noise(random, context_noise)
        )
        max_target_overspeed = profile.get("max_target_overspeed")
        if max_target_overspeed is not None and segment["curvatureLevel"] in {"medium", "high"}:
            speed = min(speed, segment["targetSpeed"] + max_target_overspeed)

        target_delta = clamp(segment["targetSpeed"] - speed, -5, 5)
        progressive_ax = (
            target_delta * 0.08
            + (-0.35 if segment["context"] == "village_approach" else 0)
            + (-0.45 if segment["context"] == "destination" else 0)
            + noise(random, 0.14)
        )
        ax = (
            progressive_ax
            - late_brake * (3.05 + random() * 0.35)
            + junction_acceleration * (2.55 + random() * 0.28)
            + sin(timestamp * 1.65) * urban_fluctuation * 0.8 * profile.get("urban_ax_scale", 1.0)
        )

        if segment["curvatureLevel"] == "high":
            curve_ay = 0.85 + sin(progress * pi) * 0.95
        elif segment["curvatureLevel"] == "medium":
            curve_ay = 0.35 + sin(progress * pi) * 0.35
        else:
            curve_ay = 0.08

        ay = (
            curve_ay
            + curve_demand * (0.7 + speed / 38) * profile.get("lateral_scale", 1.0)
            + (sin(progress * pi) * 1.05 if segment["context"] == "roundabout_or_junction" else 0)
            + sin(timestamp * 1.4) * urban_fluctuation * 0.25
            + noise(random, 0.12)
        ) * profile.get("ay_scale", 1.0)
        yaw_rate = (
            (0.13 if segment["curvatureLevel"] == "high" else 0.07 if segment["curvatureLevel"] == "medium" else 0.018)
            + curve_demand * 0.12 * profile.get("yaw_scale", 1.0)
            + (sin(progress * pi) * 0.26 if segment["context"] == "roundabout_or_junction" else 0)
            + noise(random, 0.018)
        ) * profile.get("yaw_rate_scale", 1.0)

        brake = clamp(max(0, -ax) * 0.16 + late_brake * 0.8 + (progress * 0.55 if segment["context"] == "destination" else 0), 0, 1)
        throttle = clamp(max(0, ax) * 0.18 + junction_acceleration * 0.72 + (0.25 if segment["context"] == "rural_straight" else 0.12) + noise(random, 0.04), 0, 1)

        dynamic_activation = (
            late_brake * 4.6
            + curve_demand * 3.5
            + junction_acceleration * 2.8
            + urban_fluctuation * 1.4
            + (1.2 if segment["trafficComplexity"] == "high" else 0)
        ) * profile.get("dynamic_scale", 1.0)
        heart_rate = hr_baseline + sin(timestamp / 48) * 1.8 + dynamic_activation + noise(random, 0.9) if include_wearable_data else None

        sample: dict[str, Any] = {
            "timestamp": timestamp,
            "speed": round(clamp(speed, 0, segment["speedLimit"] + 4), 2),
            "ax": round(ax, 2),
            "ay": round(ay, 2),
            "yawRate": round(yaw_rate, 3),
            "steeringAngle": round(ay * 6.4 + yaw_rate * 22 + noise(random, 1.1), 1),
            "brake": round(brake, 2),
            "throttle": round(throttle, 2),
            "roadContext": segment["context"],
            "segmentId": segment["id"],
            "segmentName": segment["name"],
            "speedLimit": segment["speedLimit"],
            "targetSpeed": segment["targetSpeed"],
            "curvatureLevel": segment["curvatureLevel"],
            "trafficComplexity": segment["trafficComplexity"],
            "expectedLateralDemand": segment["expectedLateralDemand"],
            "distanceAlongRoute": round(route_progress(timestamp), 4),
        }
        if heart_rate is not None:
            sample["heartRate"] = round(heart_rate, 1)
        samples.append(sample)

    return samples


def local_speed_range(samples: list[dict[str, Any]], index: int) -> float:
    window = samples[max(0, index - 4) : min(len(samples), index + 5)]
    speeds = [sample["speed"] for sample in window]
    return max(speeds) - min(speeds)


def acceleration_sign_changes(samples: list[dict[str, Any]], index: int) -> int:
    window = samples[max(0, index - 4) : min(len(samples), index + 5)]
    ax = [sample["ax"] for sample in window]
    changes = 0
    for i in range(1, len(ax)):
        if ax[i] != 0 and ax[i - 1] != 0 and (ax[i] > 0) != (ax[i - 1] > 0):
            changes += 1
    return changes


EVENT_SPECS: list[dict[str, Any]] = [
    {
        "type": "late_braking_before_curve",
        "evidenceKey": "peakDeceleration",
        "threshold": 3.0,
        "suggestion": "Reduce speed earlier before similar country-road curves.",
    },
    {
        "type": "high_speed_in_curve",
        "evidenceKey": "speedAboveTarget",
        "threshold": 2.5,
        "suggestion": "Settle speed before entering high-curvature sections.",
    },
    {
        "type": "unstable_cornering",
        "evidenceKey": "combinedCorneringDemand",
        "threshold": 2.2,
        "suggestion": "Use a smoother steering arc and reduce entry speed before the bend.",
    },
    {
        "type": "harsh_braking",
        "evidenceKey": "peakDeceleration",
        "threshold": 3.0,
        "suggestion": "Brake earlier and more progressively before higher-demand segments.",
    },
    {
        "type": "harsh_acceleration",
        "evidenceKey": "peakAcceleration",
        "threshold": 2.5,
        "suggestion": "Apply throttle more progressively to improve comfort and energy efficiency.",
    },
    {
        "type": "high_lateral_acceleration",
        "evidenceKey": "peakLateralAcceleration",
        "threshold": 2.0,
        "suggestion": "Reduce entry speed before corners to improve stability.",
    },
    {
        "type": "sharp_yaw_motion",
        "evidenceKey": "peakYawRate",
        "threshold": 0.35,
        "suggestion": "Use smoother steering input and avoid abrupt corrections.",
    },
    {
        "type": "unstable_speed_control",
        "evidenceKey": "localSpeedRange",
        "threshold": 4.0,
        "suggestion": "Hold a steadier following gap and use smoother pedal transitions in urban traffic.",
    },
]


CONTEXT_THRESHOLD_PROFILES: dict[str, dict[str, Any]] = {
    "campus_exit": {
        "label": "campus departure",
        "ax": 0.72,
        "ay": 0.55,
        "yaw": 0.75,
        "speed": 0.7,
        "speed_range": 0.75,
        "reason": "low-speed campus context expects gentle braking, throttle, and steering changes",
    },
    "rural_straight": {
        "label": "rural straight",
        "ax": 1.08,
        "ay": 0.85,
        "yaw": 0.9,
        "speed": 1.1,
        "speed_range": 1.25,
        "reason": "open rural straight allows more speed variation but should have low lateral demand",
    },
    "village_approach": {
        "label": "village approach",
        "ax": 0.9,
        "ay": 0.82,
        "yaw": 0.9,
        "speed": 0.72,
        "speed_range": 0.85,
        "reason": "village approach expects earlier speed reduction and lower overspeed tolerance",
    },
    "country_curve": {
        "label": "country-road bend",
        "ax": 0.95,
        "ay": 1.05,
        "yaw": 1.08,
        "speed": 0.68,
        "speed_range": 0.9,
        "reason": "higher-curvature rural bend is judged against route target speed and lateral demand",
    },
    "arterial_cruise": {
        "label": "arterial cruise",
        "ax": 1.02,
        "ay": 0.85,
        "yaw": 0.88,
        "speed": 1.0,
        "speed_range": 1.05,
        "reason": "arterial approach expects stable cruising with moderate traffic complexity",
    },
    "roundabout_or_junction": {
        "label": "junction or roundabout",
        "ax": 0.82,
        "ay": 0.9,
        "yaw": 0.86,
        "speed": 0.62,
        "speed_range": 0.72,
        "reason": "junction context expects lower speed, earlier braking, and smoother steering transitions",
    },
    "urban_arrival": {
        "label": "urban arrival",
        "ax": 0.8,
        "ay": 0.72,
        "yaw": 0.78,
        "speed": 0.65,
        "speed_range": 0.82,
        "reason": "urban arrival has lower speed tolerance but allows some stop-go variation",
    },
    "destination": {
        "label": "destination arrival",
        "ax": 0.62,
        "ay": 0.55,
        "yaw": 0.65,
        "speed": 0.55,
        "speed_range": 0.65,
        "reason": "destination arrival expects very low-speed, low-demand manoeuvring",
    },
}


CURVATURE_MULTIPLIERS = {"low": 0.82, "medium": 0.95, "high": 1.12}
TRAFFIC_MULTIPLIERS = {"low": 1.08, "medium": 1.0, "high": 0.86}
LATERAL_EXPECTATION = {"low": 0.85, "medium": 1.45, "high": 2.05}


def _spec_for(event_type: str) -> dict[str, Any]:
    return next(spec for spec in EVENT_SPECS if spec["type"] == event_type)


def _context_profile(sample: dict[str, Any]) -> dict[str, Any]:
    return CONTEXT_THRESHOLD_PROFILES.get(str(sample.get("roadContext")), CONTEXT_THRESHOLD_PROFILES["arterial_cruise"])


def speed_normalised_lateral_demand(sample: dict[str, Any]) -> float:
    speed = max(float(sample.get("speed", 0)), 0.1)
    expected_from_yaw = max(speed * abs(float(sample.get("yawRate", 0))), 0.1)
    expected_from_context = LATERAL_EXPECTATION.get(str(sample.get("expectedLateralDemand", "medium")), 1.45)
    expected = max(expected_from_yaw, expected_from_context)
    return abs(float(sample.get("ay", 0))) / expected


def context_threshold_info(event_type: str, sample: dict[str, Any]) -> dict[str, Any]:
    spec = _spec_for(event_type)
    profile = _context_profile(sample)
    speed = float(sample.get("speed", 0))
    target_speed = float(sample.get("targetSpeed", max(speed, 1)))
    speed_ratio = speed / max(target_speed, 1)
    curvature_level = str(sample.get("curvatureLevel", "medium"))
    traffic_complexity = str(sample.get("trafficComplexity", "medium"))
    curvature_multiplier = CURVATURE_MULTIPLIERS.get(curvature_level, 1.0)
    traffic_multiplier = TRAFFIC_MULTIPLIERS.get(traffic_complexity, 1.0)

    base = float(spec["threshold"])
    if event_type in {"late_braking_before_curve", "harsh_braking"}:
        threshold = base * float(profile["ax"]) * traffic_multiplier
        if speed_ratio > 1.12:
            threshold *= 0.92
        axis = "longitudinal acceleration"
    elif event_type == "harsh_acceleration":
        threshold = base * float(profile["ax"]) * (0.92 if traffic_complexity == "high" else 1.0)
        axis = "longitudinal acceleration"
    elif event_type == "high_lateral_acceleration":
        threshold = base * float(profile["ay"]) * curvature_multiplier * traffic_multiplier
        if speed_ratio > 1.1:
            threshold *= 0.92
        axis = "lateral acceleration"
    elif event_type == "sharp_yaw_motion":
        threshold = base * float(profile["yaw"]) * curvature_multiplier * traffic_multiplier
        axis = "yaw rate"
    elif event_type == "high_speed_in_curve":
        threshold = base * float(profile["speed"]) * (0.88 if curvature_level == "high" else 1.0) * traffic_multiplier
        axis = "speed above route target"
    elif event_type == "unstable_cornering":
        threshold = base * float(profile["ay"]) * curvature_multiplier * traffic_multiplier
        if speed_normalised_lateral_demand(sample) > 1.15:
            threshold *= 0.94
        axis = "combined lateral/yaw demand"
    else:
        threshold = base * float(profile["speed_range"]) * traffic_multiplier
        axis = "local speed range"

    threshold = max(threshold, base * 0.45)
    return {
        "baseThreshold": round(base, 3),
        "threshold": round(threshold, 3),
        "axis": axis,
        "contextLabel": profile["label"],
        "reason": profile["reason"],
        "speedRatioToTarget": round(speed_ratio, 2),
        "curvatureLevel": curvature_level,
        "trafficComplexity": traffic_complexity,
        "speedNormalisedLateralDemand": round(speed_normalised_lateral_demand(sample), 2),
        "thresholdMode": "context_aware_route_grounded",
    }


def segment_threshold_info(event_type: str, segment: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = sorted(
        (context_threshold_info(event_type, sample) for sample in segment),
        key=lambda item: item["threshold"],
    )
    return ranked[0]


def event_matches(event_type: str, sample: dict[str, Any], index: int, samples: list[dict[str, Any]]) -> bool:
    threshold = context_threshold_info(event_type, sample)["threshold"]
    if event_type == "late_braking_before_curve":
        next_samples = samples[index : min(len(samples), index + 18)]
        approaching_curve = any(future["roadContext"] == "country_curve" for future in next_samples)
        return sample["ax"] < -threshold and sample["roadContext"] in {"village_approach", "country_curve"} and approaching_curve
    if event_type == "high_speed_in_curve":
        return sample["curvatureLevel"] == "high" and sample["speed"] - sample["targetSpeed"] > threshold
    if event_type == "unstable_cornering":
        yaw_threshold = context_threshold_info("sharp_yaw_motion", sample)["threshold"] * 0.72
        return (
            sample["curvatureLevel"] == "high"
            and abs(sample["ay"]) + abs(sample["yawRate"]) * 2 > threshold
            and abs(sample["yawRate"]) > yaw_threshold
            and speed_normalised_lateral_demand(sample) > 0.85
        )
    if event_type == "harsh_braking":
        return sample["ax"] < -threshold
    if event_type == "harsh_acceleration":
        return sample["ax"] > threshold
    if event_type == "high_lateral_acceleration":
        return abs(sample["ay"]) > threshold and speed_normalised_lateral_demand(sample) > 0.85
    if event_type == "sharp_yaw_motion":
        return abs(sample["yawRate"]) > threshold
    if event_type == "unstable_speed_control":
        return (
            sample["roadContext"] in {"urban_arrival", "roundabout_or_junction", "village_approach"}
            and local_speed_range(samples, index) > threshold
            and acceleration_sign_changes(samples, index) >= 3
        )
    return False


def event_magnitude(spec: dict[str, Any], segment: list[dict[str, Any]], samples: list[dict[str, Any]]) -> float:
    event_type = spec["type"]
    if event_type in {"late_braking_before_curve", "harsh_braking"}:
        return max(abs(sample["ax"]) for sample in segment)
    if event_type == "high_speed_in_curve":
        return max(sample["speed"] - sample["targetSpeed"] for sample in segment)
    if event_type == "unstable_cornering":
        return max(abs(sample["ay"]) + abs(sample["yawRate"]) * 2 for sample in segment)
    if event_type == "harsh_acceleration":
        return max(abs(sample["ax"]) for sample in segment)
    if event_type == "high_lateral_acceleration":
        return max(abs(sample["ay"]) for sample in segment)
    if event_type == "sharp_yaw_motion":
        return max(abs(sample["yawRate"]) for sample in segment)
    return max(local_speed_range(samples, samples.index(sample)) for sample in segment)


def severity_from_ratio(ratio: float) -> str:
    if ratio >= 1.55:
        return "high"
    if ratio >= 1.2:
        return "medium"
    return "low"


def event_explanation(event_type: str, segment_name: str) -> str:
    if event_type == "late_braking_before_curve":
        return f"Late braking was detected before or at the beginning of {segment_name}."
    if event_type == "high_speed_in_curve":
        return f"Speed stayed above the route target through {segment_name}."
    if event_type == "unstable_cornering":
        return f"Lateral acceleration and yaw rate rose together during {segment_name}."
    if event_type == "harsh_braking":
        return f"A braking segment exceeded the harsh deceleration threshold in {segment_name}."
    if event_type == "harsh_acceleration":
        return f"Sharper throttle demand was detected in {segment_name}."
    if event_type == "high_lateral_acceleration":
        return f"Higher cornering demand was detected in {segment_name}."
    if event_type == "sharp_yaw_motion":
        return f"Yaw rate indicates an abrupt heading change in {segment_name}."
    return f"Stop-and-go speed variation was detected in {segment_name}."


def overlaps_existing(segment: list[dict[str, Any]], events: list[dict[str, Any]], event_type: str) -> bool:
    if event_type not in {"harsh_braking", "high_lateral_acceleration", "sharp_yaw_motion"}:
        return False
    for event in events:
        equivalent = (
            (event_type == "harsh_braking" and event["type"] == "late_braking_before_curve")
            or (event_type == "high_lateral_acceleration" and event["type"] == "unstable_cornering")
            or (event_type == "sharp_yaw_motion" and event["type"] == "unstable_cornering")
        )
        if equivalent and segment[0]["timestamp"] <= event["endTime"] and segment[-1]["timestamp"] >= event["startTime"]:
            return True
    return False


def build_event(spec: dict[str, Any], segment: list[dict[str, Any]], samples: list[dict[str, Any]], sequence: int) -> dict[str, Any]:
    sample = segment[0]
    magnitude = event_magnitude(spec, segment, samples)
    threshold_info = segment_threshold_info(spec["type"], segment)
    severity = severity_from_ratio(magnitude / threshold_info["threshold"])
    explanation = event_explanation(spec["type"], sample["segmentName"])

    return {
        "id": f"{spec['type']}-{sequence}",
        "type": spec["type"],
        "startTime": segment[0]["timestamp"],
        "endTime": segment[-1]["timestamp"],
        "severity": severity,
        "roadContext": sample["roadContext"],
        "segmentName": sample["segmentName"],
        "contextualExplanation": explanation,
        "shortExplanation": explanation,
        "coachingSuggestion": spec["suggestion"],
        "evidence": {
            spec["evidenceKey"]: round(magnitude, 2),
            "threshold": threshold_info["threshold"],
            "baseThreshold": threshold_info["baseThreshold"],
            "thresholdMode": threshold_info["thresholdMode"],
            "thresholdAxis": threshold_info["axis"],
            "thresholdReason": threshold_info["reason"],
            "speedRatioToTarget": threshold_info["speedRatioToTarget"],
            "speedNormalisedLateralDemand": threshold_info["speedNormalisedLateralDemand"],
            "targetSpeed": round(sample["targetSpeed"], 1),
            "speedLimit": round(sample["speedLimit"], 1),
            "roadContext": sample["roadContext"],
            "segmentName": sample["segmentName"],
            "curvatureLevel": threshold_info["curvatureLevel"],
            "trafficComplexity": threshold_info["trafficComplexity"],
            "sampleCount": len(segment),
        },
    }


def detect_risk_events(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for spec in EVENT_SPECS:
        active_segment: list[dict[str, Any]] = []
        for index, sample in enumerate(samples):
            if event_matches(spec["type"], sample, index, samples):
                active_segment.append(sample)
                continue
            if active_segment:
                if not overlaps_existing(active_segment, events, spec["type"]):
                    events.append(build_event(spec, active_segment, samples, len(events) + 1))
                active_segment = []
        if active_segment and not overlaps_existing(active_segment, events, spec["type"]):
            events.append(build_event(spec, active_segment, samples, len(events) + 1))

    strongest_by_type: dict[str, dict[str, Any]] = {}
    rank = {"low": 1, "medium": 2, "high": 3}
    for event in events:
        current = strongest_by_type.get(event["type"])
        if current is None or rank[event["severity"]] > rank[current["severity"]]:
            strongest_by_type[event["type"]] = event
    return sorted(strongest_by_type.values(), key=lambda event: event["startTime"])


def severity_penalty(events: list[dict[str, Any]]) -> float:
    penalty = 0.0
    for event in events:
        if event["severity"] == "high":
            penalty += 8
        elif event["severity"] == "medium":
            penalty += 4
        else:
            penalty += 1.5
    return penalty


def baseline_heart_rate(samples: list[dict[str, Any]]) -> float | None:
    heart_rate_samples = [sample for sample in samples if "heartRate" in sample]
    if not heart_rate_samples:
        return None
    start_time = heart_rate_samples[0]["timestamp"]
    duration = heart_rate_samples[-1]["timestamp"] - start_time
    if duration >= 60:
        baseline_window = [sample for sample in heart_rate_samples if sample["timestamp"] <= start_time + 60]
    else:
        baseline_window = heart_rate_samples[: max(1, round(len(heart_rate_samples) * 0.2))]
    return mean([sample["heartRate"] for sample in baseline_window])


def context_adaptation_score(samples: list[dict[str, Any]], events: list[dict[str, Any]]) -> float:
    speed_target_penalty = mean([max(0, sample["speed"] - sample["targetSpeed"]) * 2.2 for sample in samples])
    lateral_context_penalty = mean(
        [
            max(
                0,
                abs(sample["ay"])
                - (2.15 if sample["expectedLateralDemand"] == "high" else 1.45 if sample["expectedLateralDemand"] == "medium" else 0.8),
            )
            * 12
            for sample in samples
        ]
    )
    urban_samples = [sample for sample in samples if sample["roadContext"] == "urban_arrival"]
    urban_instability_penalty = mean([max(0, abs(sample["ax"]) - 0.9) * 7 for sample in urban_samples]) if urban_samples else 0
    curve_entry = [sample for sample in samples if sample["roadContext"] == "country_curve"][:18]
    curve_entry_penalty = mean([max(0, sample["speed"] - sample["targetSpeed"]) * 4 for sample in curve_entry]) if curve_entry else 0
    context_event_penalty = len([event for event in events if event["type"] in {"late_braking_before_curve", "high_speed_in_curve", "unstable_cornering"}]) * 4
    return clamp(100 - speed_target_penalty - lateral_context_penalty - urban_instability_penalty - curve_entry_penalty - context_event_penalty, 0, 100)


def calculate_metrics(samples: list[dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, Any]:
    speeds = [sample["speed"] for sample in samples]
    ax_values = [sample["ax"] for sample in samples]
    ay_values = [sample["ay"] for sample in samples]
    yaw_values = [sample["yawRate"] for sample in samples]
    event_penalty = severity_penalty(events)

    mean_abs_ax = mean([abs(value) for value in ax_values])
    max_abs_ax = max(abs(value) for value in ax_values)
    mean_abs_ay = mean([abs(value) for value in ay_values])
    max_abs_ay = max(abs(value) for value in ay_values)
    yaw_rate_rms = rms(yaw_values)
    longitudinal_score = clamp(100 - mean_abs_ax * 14 - max_abs_ax * 5.2 - event_penalty * 0.35, 0, 100)
    lateral_score = clamp(100 - mean_abs_ay * 15 - max_abs_ay * 6.2 - yaw_rate_rms * 32 - event_penalty * 0.3, 0, 100)
    event_safety_score = clamp(100 - event_penalty, 0, 100)
    context_score = context_adaptation_score(samples, events)
    overall_score = clamp(0.35 * longitudinal_score + 0.3 * lateral_score + 0.2 * event_safety_score + 0.15 * context_score, 0, 100)

    heart_rates = [sample["heartRate"] for sample in samples if "heartRate" in sample]
    baseline = baseline_heart_rate(samples)
    mean_hr = mean(heart_rates) if heart_rates else None

    metrics: dict[str, Any] = {
        "durationSeconds": samples[-1]["timestamp"] - samples[0]["timestamp"] if len(samples) > 1 else 0,
        "meanSpeed": mean(speeds),
        "maxSpeed": max(speeds),
        "speedStd": standard_deviation(speeds),
        "meanAbsAx": mean_abs_ax,
        "maxAbsAx": max_abs_ax,
        "meanAbsAy": mean_abs_ay,
        "maxAbsAy": max_abs_ay,
        "accelerationRms": rms(ax_values),
        "yawRateRms": yaw_rate_rms,
        "overallDrivingScore": overall_score,
        "overallSmoothnessScore": overall_score,
        "longitudinalSmoothnessScore": longitudinal_score,
        "lateralStabilityScore": lateral_score,
        "contextAdaptationScore": context_score,
        "eventSafetyScore": event_safety_score,
        "riskEventCount": len(events),
        "wearableConnected": bool(heart_rates),
    }
    if heart_rates:
        metrics.update(
            {
                "meanHeartRate": mean_hr,
                "maxHeartRate": max(heart_rates),
                "baselineHeartRate": baseline,
                "heartRateDeltaPercent": ((mean_hr - baseline) / baseline) * 100 if baseline and mean_hr else None,
            }
        )
    return metrics


def generate_demo_session(
    include_wearable_data: bool = False,
    seed: int | None = None,
    scenario: str = "mixed_route_review",
    duration_seconds: int | None = None,
    sample_rate_hz: int = 1,
) -> dict[str, Any]:
    config = scenario_config(scenario)
    resolved_seed = config["seed"] if seed is None else seed
    resolved_scenario = scenario if scenario in SCENARIOS else "mixed_route_review"
    resolved_wearable = config["defaultWearable"] if resolved_scenario in {"wearable_connected", "wearable_not_connected"} else include_wearable_data
    profile = generated_profile(resolved_seed) if resolved_scenario == "agent_generated" else config["profile"]
    samples = generate_samples(resolved_wearable, resolved_seed, duration_seconds, sample_rate_hz, profile)
    events = detect_risk_events(samples)
    metrics = calculate_metrics(samples, events)
    return {
        "id": f"cranfield-mk-{resolved_scenario}-{resolved_seed}",
        "title": "Generated Cranfield to Milton Keynes Midsummer Place route review",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "scenario": {
            "key": resolved_scenario,
            "label": config["label"],
            "seed": resolved_seed,
            "expectedEvents": [event["type"] for event in events] if resolved_scenario == "agent_generated" else config["expectedEvents"],
            "mapAnchors": config["mapAnchors"],
            "generationMode": "seeded_random" if resolved_scenario == "agent_generated" else "fixed_ground_truth",
        },
        "route": route_with_geometry(),
        "samples": samples,
        "events": events,
        "metrics": metrics,
    }
