import pandas as pd

from src.analysis.event_detector import detect_events


def test_detect_events_returns_rule_based_events() -> None:
    df = pd.DataFrame(
        {
            "timestamp": [0, 1, 2, 3, 4, 5],
            "ax": [0.0, -3.2, -3.5, 2.8, 0.0, 0.0],
            "ay": [0.0, 0.1, 0.2, 2.2, 2.3, 0.0],
            "yaw_rate": [0.0, 0.1, 0.2, 0.1, 0.4, 0.0],
            "heart_rate": [70.0, 71.0, 72.0, 82.0, 84.0, 70.0],
        }
    )

    events = detect_events(df, baseline_hr=70.0)
    event_types = {event["type"] for event in events}

    assert "harsh_braking" in event_types
    assert "harsh_acceleration" in event_types
    assert "high_lateral_acceleration" in event_types
    assert "sharp_yaw_motion" in event_types
    assert "elevated_physiological_activation" in event_types

    braking = next(event for event in events if event["type"] == "harsh_braking")
    assert braking["start_time"] == 1.0
    assert braking["end_time"] == 2.0
    assert braking["severity"] in {"low", "medium", "high"}
    assert "peak_magnitude" in braking["evidence"]


def test_detect_events_returns_empty_when_no_rules_match() -> None:
    df = pd.DataFrame(
        {
            "timestamp": [0, 1, 2],
            "ax": [0.0, 0.1, -0.1],
            "ay": [0.0, 0.1, -0.1],
            "yaw_rate": [0.0, 0.01, -0.01],
            "heart_rate": [70.0, 71.0, 70.0],
        }
    )

    assert detect_events(df, baseline_hr=70.0) == []
