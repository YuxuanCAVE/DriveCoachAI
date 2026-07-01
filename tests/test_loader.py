from pathlib import Path

import pandas as pd
import pytest

from src.data.loader import load_heart_rate, load_vehicle_log
from src.data.synchronizer import synchronize_to_1hz
from src.data.validator import validate_heart_rate_data, validate_vehicle_data


def test_load_vehicle_log_returns_dataframe(tmp_path: Path) -> None:
    csv_path = tmp_path / "vehicle_log.csv"
    csv_path.write_text("timestamp,speed,ax,ay,yaw_rate\n0,1,0.1,0.2,0.01\n", encoding="utf-8")

    df = load_vehicle_log(csv_path)

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["timestamp", "speed", "ax", "ay", "yaw_rate"]


def test_load_missing_file_has_clear_error(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="vehicle_log.csv file not found"):
        load_vehicle_log(tmp_path / "missing.csv")


def test_validate_vehicle_data_interpolates_numeric_values() -> None:
    df = pd.DataFrame(
        {
            "timestamp": [0, 1, 2],
            "speed": [10.0, None, 12.0],
            "ax": [0.0, 1.0, 0.0],
            "ay": [0.1, None, 0.3],
            "yaw_rate": [0.01, 0.02, 0.03],
        }
    )

    cleaned = validate_vehicle_data(df)

    assert cleaned["speed"].iloc[1] == pytest.approx(11.0)
    assert cleaned["ay"].iloc[1] == pytest.approx(0.2)


def test_validate_heart_rate_rejects_non_monotonic_timestamp() -> None:
    df = pd.DataFrame({"timestamp": [0, 2, 1], "heart_rate": [70, 71, 72]})

    with pytest.raises(ValueError, match="timestamp must be monotonically increasing"):
        validate_heart_rate_data(df)


def test_load_heart_rate_returns_dataframe(tmp_path: Path) -> None:
    csv_path = tmp_path / "heart_rate.csv"
    csv_path.write_text("timestamp,heart_rate\n0,72\n1,73\n", encoding="utf-8")

    df = load_heart_rate(csv_path)

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["timestamp", "heart_rate"]


def test_synchronize_to_1hz_aligns_overlapping_time_window() -> None:
    vehicle_df = pd.DataFrame(
        {
            "timestamp": [0.0, 0.5, 1.5, 2.0],
            "speed": [10.0, 11.0, 13.0, 14.0],
            "ax": [0.0, 0.2, 0.3, 0.0],
            "ay": [0.1, 0.2, 0.3, 0.2],
            "yaw_rate": [0.01, 0.02, 0.03, 0.01],
        }
    )
    heart_rate_df = pd.DataFrame({"timestamp": [1.0, 2.0], "heart_rate": [70.0, 72.0]})

    synced = synchronize_to_1hz(vehicle_df, heart_rate_df)

    assert synced["timestamp"].tolist() == [1.0, 2.0]
    assert "speed" in synced.columns
    assert "heart_rate" in synced.columns
    assert synced["heart_rate"].tolist() == [70.0, 72.0]
