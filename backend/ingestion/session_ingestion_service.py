from __future__ import annotations

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.ingestion.route_geometry import (
    CRANFIELD_TO_MK_GEOMETRY,
    interpolate_route_position,
    route_curvature_profile,
    route_distance_m,
)
from backend.services.demo_session_service import (
    ROUTE,
    calculate_metrics,
    detect_risk_events,
    generate_samples,
    generated_profile,
    scenario_config,
    segment_at,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class IngestionError(ValueError):
    pass


def _resolve_csv_path(csv_path: str) -> Path:
    path = Path(csv_path)
    resolved = path if path.is_absolute() else PROJECT_ROOT / path
    resolved = resolved.resolve()
    project_root = PROJECT_ROOT.resolve()
    if project_root not in resolved.parents and resolved != project_root:
        raise IngestionError("CSV path must be inside the project directory.")
    if not resolved.exists():
        raise IngestionError(f"CSV path does not exist: {resolved}")
    if resolved.suffix.lower() != ".csv":
        raise IngestionError("CSV path must point to a .csv file.")
    return resolved


def _as_float(row: dict[str, Any], *keys: str, default: float | None = None) -> float:
    for key in keys:
        value = row.get(key)
        if value is not None and value != "":
            try:
                return float(value)
            except (TypeError, ValueError) as error:
                raise IngestionError(f"Column '{key}' must be numeric.") from error
    if default is not None:
        return default
    raise IngestionError(f"Missing required numeric column: {'/'.join(keys)}")


def _segment_metadata(timestamp: float, distance_progress: float | None = None) -> dict[str, Any]:
    segment = segment_at(timestamp)
    progress = distance_progress if distance_progress is not None else min(max(timestamp / ROUTE["segments"][-1]["endTime"], 0), 1)
    position = interpolate_route_position(progress)
    return {
        "roadContext": segment["context"],
        "segmentId": segment["id"],
        "segmentName": segment["name"],
        "speedLimit": segment["speedLimit"],
        "targetSpeed": segment["targetSpeed"],
        "curvatureLevel": segment["curvatureLevel"],
        "trafficComplexity": segment["trafficComplexity"],
        "expectedLateralDemand": segment["expectedLateralDemand"],
        "distanceAlongRoute": round(progress, 4),
        "lat": position["lat"],
        "lon": position["lon"],
    }


def _normalise_sample(row: dict[str, Any], index: int, total: int) -> dict[str, Any]:
    timestamp = _as_float(row, "timestamp", "time", "t")
    progress = row.get("distanceAlongRoute")
    distance_progress = float(progress) if progress not in {None, ""} else None
    metadata = _segment_metadata(timestamp, distance_progress)
    sample = {
        "timestamp": timestamp,
        "speed": round(_as_float(row, "speed"), 3),
        "ax": round(_as_float(row, "ax", "longitudinal_acceleration"), 3),
        "ay": round(_as_float(row, "ay", "lateral_acceleration"), 3),
        "yawRate": round(_as_float(row, "yawRate", "yaw_rate"), 4),
        "steeringAngle": round(_as_float(row, "steeringAngle", "steering_angle", default=0.0), 3),
        "brake": round(_as_float(row, "brake", default=max(0.0, -_as_float(row, "ax", "longitudinal_acceleration")) * 0.15), 3),
        "throttle": round(_as_float(row, "throttle", default=max(0.0, _as_float(row, "ax", "longitudinal_acceleration")) * 0.16), 3),
        **metadata,
    }
    road_context = row.get("roadContext") or row.get("road_context") or row.get("road_type")
    if road_context:
        sample["roadContext"] = str(road_context)
    segment_name = row.get("segmentName") or row.get("segment_name")
    if segment_name:
        sample["segmentName"] = str(segment_name)
    heart_rate = row.get("heartRate") or row.get("heart_rate")
    if heart_rate not in {None, ""}:
        sample["heartRate"] = round(float(heart_rate), 1)
    if "lat" in row and "lon" in row and row.get("lat") not in {None, ""} and row.get("lon") not in {None, ""}:
        sample["lat"] = round(float(row["lat"]), 6)
        sample["lon"] = round(float(row["lon"]), 6)
    return sample


def _normalise_samples(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        raise IngestionError("At least one telemetry sample is required.")
    samples = [_normalise_sample(row, index, len(rows)) for index, row in enumerate(rows)]
    samples.sort(key=lambda sample: sample["timestamp"])
    for previous, current in zip(samples, samples[1:]):
        if current["timestamp"] <= previous["timestamp"]:
            raise IngestionError("Timestamps must be strictly increasing after sorting.")
    return samples


def _read_csv_samples(csv_path: str) -> list[dict[str, Any]]:
    resolved = _resolve_csv_path(csv_path)
    with resolved.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _route_with_geometry() -> dict[str, Any]:
    return {
        **ROUTE,
        "distanceMeters": round(route_distance_m()),
        "routeSource": "cached_osm_osrm_grounded_geometry",
        "routeGeometry": CRANFIELD_TO_MK_GEOMETRY,
        "curvatureProfile": route_curvature_profile(),
    }


def _attach_route_positions(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    positioned = []
    for sample in samples:
        progress = float(sample.get("distanceAlongRoute", 0))
        position = interpolate_route_position(progress)
        positioned.append({**sample, "lat": position["lat"], "lon": position["lon"]})
    return positioned


def _build_trip(
    samples: list[dict[str, Any]],
    mode: str,
    seed: int | None,
    scenario: str,
    provenance: dict[str, Any],
) -> dict[str, Any]:
    events = detect_risk_events(samples)
    metrics = calculate_metrics(samples, events)
    trip_seed = seed if seed is not None else 0
    return {
        "id": f"analyse-session-{mode}-{scenario}-{trip_seed}-{int(datetime.now(timezone.utc).timestamp())}",
        "title": "Analysed Cranfield to Milton Keynes Midsummer Place session",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "scenario": {
            "key": scenario,
            "label": "Route-grounded ingestion" if mode == "route_simulation" else "Telemetry ingestion",
            "seed": seed,
            "expectedEvents": [event["type"] for event in events],
            "mapAnchors": [event["segmentName"] for event in events[:4]],
            "generationMode": mode,
        },
        "provenance": provenance,
        "route": _route_with_geometry(),
        "samples": samples,
        "events": events,
        "metrics": metrics,
    }


def analyse_session(request: dict[str, Any]) -> dict[str, Any]:
    mode = request.get("mode")
    include_wearable = bool(request.get("includeWearableData", False))
    seed = request.get("seed")
    scenario = str(request.get("scenario") or "route_grounded")

    if mode == "telemetry_json":
        samples = _normalise_samples(list(request.get("samples") or []))
        provenance = {
            "dataSource": "telemetry_json",
            "routeSource": "provided_or_inferred_route_context",
            "notRealDriverData": False,
            "assumptions": ["Samples were provided by API request and normalized into the DriveCoach SampleTrip contract."],
        }
        return _build_trip(samples, mode, seed, scenario, provenance)

    if mode == "csv_path":
        csv_path = request.get("vehicleCsvPath")
        if not csv_path:
            raise IngestionError("vehicleCsvPath is required for csv_path mode.")
        samples = _normalise_samples(_read_csv_samples(str(csv_path)))
        provenance = {
            "dataSource": "csv_path",
            "vehicleCsvPath": str(csv_path),
            "routeSource": "provided_or_inferred_route_context",
            "notRealDriverData": False,
            "assumptions": ["CSV rows were normalized into the DriveCoach SampleTrip contract."],
        }
        return _build_trip(samples, mode, seed, scenario, provenance)

    if mode == "route_simulation":
        resolved_seed = int(seed if seed is not None else 7201)
        config = scenario_config("agent_generated" if scenario == "agent_generated" else "mixed_route_review")
        profile = generated_profile(resolved_seed) if scenario in {"route_grounded", "agent_generated"} else config["profile"]
        duration_seconds = request.get("durationSeconds")
        sample_rate_hz = int(request.get("sampleRateHz") or 1)
        samples = _attach_route_positions(
            generate_samples(include_wearable, resolved_seed, duration_seconds, sample_rate_hz, profile)
        )
        provenance = {
            "dataSource": "route_grounded_synthetic",
            "routeSource": "cached_osm_osrm_grounded_geometry",
            "seed": resolved_seed,
            "notRealDriverData": True,
            "assumptions": [
                "Route geometry is cached from the Cranfield University to Milton Keynes Midsummer Place map reference.",
                "Speed targets are generated from segment context: campus, rural road, curve, junction, urban arrival.",
                "Signals use simple dynamics: ax from speed changes, yawRate from curvature demand, ay from speed and curvature.",
                "Hazards are synthetic scenario perturbations, not real driver behaviour.",
            ],
        }
        return _build_trip(samples, mode, resolved_seed, scenario, provenance)

    raise IngestionError("Unsupported analyse-session mode. Use telemetry_json, csv_path, or route_simulation.")

