import numpy as np
import pandas as pd


def _rms(series: pd.Series) -> float:
    values = series.dropna().to_numpy(dtype=float)
    if len(values) == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(values))))


def _score_from_rms(rms_value: float, comfort_limit: float) -> float:
    if comfort_limit <= 0:
        raise ValueError("comfort_limit must be positive.")
    score = 100.0 * (1.0 - min(rms_value / comfort_limit, 1.0))
    return round(score, 2)


def compute_behaviour_metrics(df: pd.DataFrame) -> dict[str, float]:
    """Compute transparent vehicle behaviour metrics from synchronized or vehicle-only data."""
    required = ["speed", "ax", "ay", "yaw_rate"]
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise ValueError(f"Missing required behaviour metric columns: {', '.join(missing)}")

    acceleration_rms = _rms(df["ax"])
    yaw_rate_rms = _rms(df["yaw_rate"])
    lateral_rms = _rms(df["ay"])

    return {
        "mean_speed": float(df["speed"].mean()),
        "max_speed": float(df["speed"].max()),
        "speed_std": float(df["speed"].std(ddof=0)),
        "mean_abs_ax": float(df["ax"].abs().mean()),
        "max_abs_ax": float(df["ax"].abs().max()),
        "mean_abs_ay": float(df["ay"].abs().mean()),
        "max_abs_ay": float(df["ay"].abs().max()),
        "acceleration_rms": acceleration_rms,
        "yaw_rate_rms": yaw_rate_rms,
        "lateral_stability_score": _score_from_rms(lateral_rms, comfort_limit=2.5),
        "longitudinal_smoothness_score": _score_from_rms(acceleration_rms, comfort_limit=3.0),
    }
