import pandas as pd
import pytest

from src.analysis.behaviour_metrics import compute_behaviour_metrics


def test_compute_behaviour_metrics() -> None:
    df = pd.DataFrame(
        {
            "speed": [10.0, 12.0, 14.0],
            "ax": [0.0, 1.0, -1.0],
            "ay": [0.0, 0.5, -0.5],
            "yaw_rate": [0.0, 0.1, -0.1],
        }
    )

    metrics = compute_behaviour_metrics(df)

    assert metrics["mean_speed"] == pytest.approx(12.0)
    assert metrics["max_speed"] == pytest.approx(14.0)
    assert metrics["speed_std"] == pytest.approx(1.632993, rel=1e-5)
    assert metrics["mean_abs_ax"] == pytest.approx(2 / 3)
    assert metrics["max_abs_ay"] == pytest.approx(0.5)
    assert 0 <= metrics["lateral_stability_score"] <= 100
    assert 0 <= metrics["longitudinal_smoothness_score"] <= 100


def test_compute_behaviour_metrics_requires_columns() -> None:
    df = pd.DataFrame({"speed": [1.0]})

    with pytest.raises(ValueError, match="Missing required behaviour metric columns"):
        compute_behaviour_metrics(df)
