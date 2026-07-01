import pandas as pd
import pytest

from src.analysis.physiological_metrics import compute_baseline_hr, compute_physiological_metrics


def test_baseline_uses_first_60_seconds_when_available() -> None:
    df = pd.DataFrame(
        {
            "timestamp": [0, 30, 60, 90],
            "heart_rate": [70.0, 72.0, 74.0, 90.0],
        }
    )

    assert compute_baseline_hr(df) == pytest.approx(72.0)


def test_physiological_metrics_with_rr_interval() -> None:
    df = pd.DataFrame(
        {
            "timestamp": [0, 1, 2, 3],
            "heart_rate": [70.0, 72.0, 74.0, 76.0],
            "rr_interval": [0.86, 0.84, 0.82, 0.80],
        }
    )

    metrics = compute_physiological_metrics(df, rolling_window=2)

    assert metrics["mean_hr"] == pytest.approx(73.0)
    assert metrics["max_hr"] == pytest.approx(76.0)
    assert metrics["min_hr"] == pytest.approx(70.0)
    assert metrics["baseline_hr"] == pytest.approx(70.0)
    assert metrics["rmssd"] is not None
    assert len(metrics["rolling_hr_mean"]) == 4


def test_physiological_metrics_without_rr_interval_returns_none() -> None:
    df = pd.DataFrame({"timestamp": [0, 1, 2], "heart_rate": [70.0, 72.0, 74.0]})

    metrics = compute_physiological_metrics(df)

    assert metrics["rmssd"] is None
