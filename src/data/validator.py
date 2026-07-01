from collections.abc import Iterable

import pandas as pd


REQUIRED_VEHICLE_COLUMNS = ["timestamp", "speed", "ax", "ay", "yaw_rate"]
OPTIONAL_VEHICLE_COLUMNS = ["steering_angle", "automation_status", "road_type"]
REQUIRED_HEART_RATE_COLUMNS = ["timestamp", "heart_rate"]
OPTIONAL_HEART_RATE_COLUMNS = ["rr_interval"]

MOSTLY_MISSING_THRESHOLD = 0.5


def _check_required_columns(df: pd.DataFrame, required_columns: Iterable[str], dataset_name: str) -> None:
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"{dataset_name} is missing required columns: {', '.join(missing)}")


def _coerce_numeric(df: pd.DataFrame, columns: Iterable[str], dataset_name: str) -> pd.DataFrame:
    cleaned = df.copy()
    for column in columns:
        if column in cleaned.columns:
            cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
            if cleaned[column].isna().mean() > MOSTLY_MISSING_THRESHOLD:
                raise ValueError(
                    f"{dataset_name} column '{column}' is mostly missing or non-numeric "
                    f"after parsing."
                )
    return cleaned


def _validate_timestamp(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    cleaned = df.copy()
    cleaned["timestamp"] = pd.to_numeric(cleaned["timestamp"], errors="coerce")
    before_drop = len(cleaned)
    cleaned = cleaned.dropna(subset=["timestamp"]).copy()
    if cleaned.empty:
        raise ValueError(f"{dataset_name} has no valid timestamp values.")

    dropped = before_drop - len(cleaned)
    if dropped > before_drop * MOSTLY_MISSING_THRESHOLD:
        raise ValueError(f"{dataset_name} has mostly missing or invalid timestamp values.")

    if not cleaned["timestamp"].is_monotonic_increasing:
        raise ValueError(f"{dataset_name} timestamp must be monotonically increasing.")
    return cleaned


def _interpolate_numeric_signals(
    df: pd.DataFrame,
    numeric_columns: Iterable[str],
) -> pd.DataFrame:
    cleaned = df.copy()
    columns = [column for column in numeric_columns if column in cleaned.columns and column != "timestamp"]
    if not columns:
        return cleaned

    cleaned[columns] = cleaned[columns].interpolate(method="linear", limit_direction="both")
    return cleaned


def validate_vehicle_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean vehicle log data."""
    _check_required_columns(df, REQUIRED_VEHICLE_COLUMNS, "vehicle_log")
    cleaned = _validate_timestamp(df, "vehicle_log")
    cleaned = _coerce_numeric(cleaned, REQUIRED_VEHICLE_COLUMNS + ["steering_angle"], "vehicle_log")
    cleaned = _interpolate_numeric_signals(cleaned, REQUIRED_VEHICLE_COLUMNS + ["steering_angle"])
    cleaned = cleaned.dropna(subset=["speed", "ax", "ay", "yaw_rate"]).reset_index(drop=True)
    if cleaned.empty:
        raise ValueError("vehicle_log has no valid signal rows after cleaning.")
    return cleaned


def validate_heart_rate_data(df: pd.DataFrame) -> pd.DataFrame:
    """Validate and clean heart rate data."""
    _check_required_columns(df, REQUIRED_HEART_RATE_COLUMNS, "heart_rate")
    cleaned = _validate_timestamp(df, "heart_rate")
    cleaned = _coerce_numeric(cleaned, REQUIRED_HEART_RATE_COLUMNS + ["rr_interval"], "heart_rate")
    cleaned = _interpolate_numeric_signals(cleaned, REQUIRED_HEART_RATE_COLUMNS + ["rr_interval"])
    cleaned = cleaned.dropna(subset=["heart_rate"]).reset_index(drop=True)
    if cleaned.empty:
        raise ValueError("heart_rate has no valid signal rows after cleaning.")
    return cleaned
