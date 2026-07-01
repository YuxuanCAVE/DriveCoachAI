import pandas as pd


def _resample_to_1hz(df: pd.DataFrame, value_columns: list[str], method: str) -> pd.DataFrame:
    if df.empty:
        raise ValueError("Cannot resample an empty DataFrame.")

    working = df[["timestamp", *value_columns]].copy()
    working["timestamp"] = pd.to_timedelta(working["timestamp"], unit="s")
    working = working.set_index("timestamp").sort_index()
    working = working.groupby(level=0).mean(numeric_only=True)

    resampled = working.resample("1s").mean()
    if method == "vehicle":
        resampled = resampled.interpolate(method="time", limit_direction="both")
    elif method == "heart_rate":
        resampled = resampled.interpolate(method="time", limit_direction="both").ffill().bfill()
    else:
        raise ValueError(f"Unsupported resampling method: {method}")

    resampled = resampled.reset_index()
    resampled["timestamp"] = resampled["timestamp"].dt.total_seconds()
    return resampled


def synchronize_to_1hz(vehicle_df: pd.DataFrame, heart_rate_df: pd.DataFrame) -> pd.DataFrame:
    """Align validated vehicle and heart rate data on a shared 1 Hz timestamp grid."""
    vehicle_columns = [
        column
        for column in ["speed", "ax", "ay", "yaw_rate", "steering_angle"]
        if column in vehicle_df.columns
    ]
    heart_rate_columns = [
        column
        for column in ["heart_rate", "rr_interval"]
        if column in heart_rate_df.columns
    ]

    vehicle_1hz = _resample_to_1hz(vehicle_df, vehicle_columns, method="vehicle")
    heart_rate_1hz = _resample_to_1hz(heart_rate_df, heart_rate_columns, method="heart_rate")

    start_time = max(vehicle_1hz["timestamp"].min(), heart_rate_1hz["timestamp"].min())
    end_time = min(vehicle_1hz["timestamp"].max(), heart_rate_1hz["timestamp"].max())
    if start_time > end_time:
        raise ValueError("Vehicle and heart rate data do not overlap in time.")

    vehicle_1hz = vehicle_1hz[(vehicle_1hz["timestamp"] >= start_time) & (vehicle_1hz["timestamp"] <= end_time)]
    heart_rate_1hz = heart_rate_1hz[
        (heart_rate_1hz["timestamp"] >= start_time) & (heart_rate_1hz["timestamp"] <= end_time)
    ]

    merged = pd.merge(vehicle_1hz, heart_rate_1hz, on="timestamp", how="inner")
    return merged.reset_index(drop=True)
