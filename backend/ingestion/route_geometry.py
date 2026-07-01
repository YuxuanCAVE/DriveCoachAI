from __future__ import annotations

from math import atan2, cos, radians, sin, sqrt
from typing import Any


# Cached route grounding for Cranfield University -> Milton Keynes Midsummer Place.
# Coordinates are approximate waypoints along the supplied route reference, intended
# for repeatable synthetic telemetry rather than turn-by-turn navigation.
CRANFIELD_TO_MK_GEOMETRY: list[dict[str, Any]] = [
    {"label": "Cranfield University", "lat": 52.0732, "lon": -0.6281, "context": "campus_exit"},
    {"label": "College Road / Cranfield Airport", "lat": 52.0752, "lon": -0.6418, "context": "campus_exit"},
    {"label": "Cranfield Road rural link", "lat": 52.0834, "lon": -0.6676, "context": "rural_straight"},
    {"label": "North Crawley", "lat": 52.0919, "lon": -0.6898, "context": "village_approach"},
    {"label": "Newport Road rural bend", "lat": 52.0838, "lon": -0.7169, "context": "country_curve"},
    {"label": "Broughton", "lat": 52.0618, "lon": -0.7158, "context": "arterial_cruise"},
    {"label": "Willen / Broughton approach", "lat": 52.0591, "lon": -0.7453, "context": "arterial_cruise"},
    {"label": "A422 / Monks Way junction", "lat": 52.0575, "lon": -0.7663, "context": "roundabout_or_junction"},
    {"label": "Milton Keynes grid-road arrival", "lat": 52.0493, "lon": -0.7739, "context": "urban_arrival"},
    {"label": "Milton Keynes Midsummer Place", "lat": 52.0418, "lon": -0.7597, "context": "destination"},
]


def _project(point: dict[str, Any], reference_lat: float) -> tuple[float, float]:
    lat = radians(float(point["lat"]))
    lon = radians(float(point["lon"]))
    earth_radius = 6_371_000
    x = earth_radius * lon * cos(radians(reference_lat))
    y = earth_radius * lat
    return x, y


def _distance_m(a: dict[str, Any], b: dict[str, Any]) -> float:
    reference_lat = (float(a["lat"]) + float(b["lat"])) / 2
    ax, ay = _project(a, reference_lat)
    bx, by = _project(b, reference_lat)
    return sqrt((bx - ax) ** 2 + (by - ay) ** 2)


def _bearing(a: dict[str, Any], b: dict[str, Any]) -> float:
    reference_lat = (float(a["lat"]) + float(b["lat"])) / 2
    ax, ay = _project(a, reference_lat)
    bx, by = _project(b, reference_lat)
    return atan2(by - ay, bx - ax)


def _angle_delta(a: float, b: float) -> float:
    delta = abs(a - b)
    while delta > 3.14159:
        delta = abs(delta - 2 * 3.14159)
    return delta


def route_distance_m() -> float:
    return sum(_distance_m(a, b) for a, b in zip(CRANFIELD_TO_MK_GEOMETRY, CRANFIELD_TO_MK_GEOMETRY[1:]))


def route_curvature_profile() -> list[dict[str, Any]]:
    profile: list[dict[str, Any]] = []
    for index, point in enumerate(CRANFIELD_TO_MK_GEOMETRY):
        if index == 0 or index == len(CRANFIELD_TO_MK_GEOMETRY) - 1:
            curvature = 0.0
        else:
            inbound = _bearing(CRANFIELD_TO_MK_GEOMETRY[index - 1], point)
            outbound = _bearing(point, CRANFIELD_TO_MK_GEOMETRY[index + 1])
            curvature = _angle_delta(inbound, outbound)
        profile.append({**point, "curvature": round(curvature, 3)})
    return profile


def interpolate_route_position(progress: float) -> dict[str, float]:
    clamped_progress = min(max(progress, 0.0), 1.0)
    distances = [_distance_m(a, b) for a, b in zip(CRANFIELD_TO_MK_GEOMETRY, CRANFIELD_TO_MK_GEOMETRY[1:])]
    total = sum(distances)
    target = clamped_progress * total
    travelled = 0.0

    for index, segment_distance in enumerate(distances):
        if travelled + segment_distance >= target:
            local = 0.0 if segment_distance == 0 else (target - travelled) / segment_distance
            start = CRANFIELD_TO_MK_GEOMETRY[index]
            end = CRANFIELD_TO_MK_GEOMETRY[index + 1]
            return {
                "lat": round(float(start["lat"]) + (float(end["lat"]) - float(start["lat"])) * local, 6),
                "lon": round(float(start["lon"]) + (float(end["lon"]) - float(start["lon"])) * local, 6),
            }
        travelled += segment_distance

    final = CRANFIELD_TO_MK_GEOMETRY[-1]
    return {"lat": round(float(final["lat"]), 6), "lon": round(float(final["lon"]), 6)}

