from collections.abc import Callable

import pandas as pd

from src.analysis.physiological_metrics import compute_baseline_hr


def _severity_from_ratio(ratio: float) -> str:
    if ratio >= 1.5:
        return "high"
    if ratio >= 1.2:
        return "medium"
    return "low"


def _contiguous_groups(mask: pd.Series) -> list[list[int]]:
    true_indices = mask[mask].index.to_list()
    if not true_indices:
        return []

    groups: list[list[int]] = [[true_indices[0]]]
    for index in true_indices[1:]:
        previous = groups[-1][-1]
        if index == previous + 1:
            groups[-1].append(index)
        else:
            groups.append([index])
    return groups


def _detect_threshold_events(
    df: pd.DataFrame,
    event_type: str,
    mask: pd.Series,
    value_column: str,
    threshold: float,
    magnitude_fn: Callable[[pd.Series], pd.Series],
) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for group in _contiguous_groups(mask):
        segment = df.loc[group]
        magnitudes = magnitude_fn(segment[value_column])
        peak_index = magnitudes.idxmax()
        magnitude = float(magnitudes.loc[peak_index])
        ratio = magnitude / threshold if threshold else 1.0
        events.append(
            {
                "type": event_type,
                "start_time": float(segment["timestamp"].iloc[0]),
                "end_time": float(segment["timestamp"].iloc[-1]),
                "severity": _severity_from_ratio(ratio),
                "evidence": {
                    "column": value_column,
                    "threshold": threshold,
                    "peak_value": float(segment.loc[peak_index, value_column]),
                    "peak_magnitude": magnitude,
                },
            }
        )
    return events


def detect_events(df: pd.DataFrame, baseline_hr: float | None = None) -> list[dict[str, object]]:
    """Detect rule-based driving and physiological activation events."""
    required = ["timestamp", "ax", "ay", "yaw_rate"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required event detection columns: {', '.join(missing)}")

    working = df.reset_index(drop=True).copy()
    events: list[dict[str, object]] = []

    events.extend(
        _detect_threshold_events(
            working,
            "harsh_braking",
            working["ax"] < -3.0,
            "ax",
            3.0,
            lambda series: series.abs(),
        )
    )
    events.extend(
        _detect_threshold_events(
            working,
            "harsh_acceleration",
            working["ax"] > 2.5,
            "ax",
            2.5,
            lambda series: series.abs(),
        )
    )
    events.extend(
        _detect_threshold_events(
            working,
            "high_lateral_acceleration",
            working["ay"].abs() > 2.0,
            "ay",
            2.0,
            lambda series: series.abs(),
        )
    )
    events.extend(
        _detect_threshold_events(
            working,
            "sharp_yaw_motion",
            working["yaw_rate"].abs() > 0.35,
            "yaw_rate",
            0.35,
            lambda series: series.abs(),
        )
    )

    if "heart_rate" in working.columns:
        baseline = compute_baseline_hr(working) if baseline_hr is None else baseline_hr
        activation_threshold = baseline * 1.15
        events.extend(
            _detect_threshold_events(
                working,
                "elevated_physiological_activation",
                working["heart_rate"] > activation_threshold,
                "heart_rate",
                activation_threshold,
                lambda series: series,
            )
        )
        for event in events:
            if event["type"] == "elevated_physiological_activation":
                event["evidence"]["baseline_hr"] = baseline

    return sorted(events, key=lambda event: (event["start_time"], event["type"]))
