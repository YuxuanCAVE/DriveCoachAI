import numpy as np
import pandas as pd


def compute_baseline_hr(df: pd.DataFrame) -> float:
    """Use the first 60 seconds when available, otherwise the first 20% of samples."""
    if "timestamp" not in df.columns or "heart_rate" not in df.columns:
        raise ValueError("Missing required physiological metric columns: timestamp, heart_rate")
    if df.empty:
        raise ValueError("Cannot compute baseline heart rate from an empty DataFrame.")

    sorted_df = df.sort_values("timestamp")
    start_time = float(sorted_df["timestamp"].min())
    end_time = float(sorted_df["timestamp"].max())
    if end_time - start_time >= 60.0:
        baseline_window = sorted_df[sorted_df["timestamp"] <= start_time + 60.0]
    else:
        window_size = max(1, int(np.ceil(len(df) * 0.2)))
        baseline_window = sorted_df.head(window_size)

    return float(baseline_window["heart_rate"].mean())


def compute_rmssd(df: pd.DataFrame) -> float | None:
    if "rr_interval" not in df.columns:
        return None
    rr_values = df["rr_interval"].dropna().to_numpy(dtype=float)
    if len(rr_values) < 2:
        return None
    successive_differences = np.diff(rr_values)
    return float(np.sqrt(np.mean(np.square(successive_differences))))


def compute_physiological_metrics(df: pd.DataFrame, rolling_window: int = 30) -> dict[str, object]:
    """Compute heart rate indicators of physiological activation."""
    if "heart_rate" not in df.columns:
        raise ValueError("Missing required physiological metric column: heart_rate")
    if rolling_window <= 0:
        raise ValueError("rolling_window must be positive.")

    baseline_hr = compute_baseline_hr(df)
    mean_hr = float(df["heart_rate"].mean())

    rolling_hr_mean = df["heart_rate"].rolling(window=rolling_window, min_periods=1).mean()
    rolling_hr_std = df["heart_rate"].rolling(window=rolling_window, min_periods=2).std(ddof=0).fillna(0.0)

    return {
        "mean_hr": mean_hr,
        "max_hr": float(df["heart_rate"].max()),
        "min_hr": float(df["heart_rate"].min()),
        "std_hr": float(df["heart_rate"].std(ddof=0)),
        "baseline_hr": baseline_hr,
        "hr_delta_percent": float(((mean_hr - baseline_hr) / baseline_hr) * 100.0) if baseline_hr else 0.0,
        "rolling_hr_mean": rolling_hr_mean,
        "rolling_hr_std": rolling_hr_std,
        "rmssd": compute_rmssd(df),
    }
