from pathlib import Path

import numpy as np
import pandas as pd


def generate_sample_data(output_dir: str | Path | None = None, duration_seconds: int = 300) -> tuple[Path, Path]:
    """Generate realistic sample vehicle and heart rate CSV files with artificial events."""
    if duration_seconds < 120:
        raise ValueError("duration_seconds must be at least 120 to include baseline and event periods.")

    project_root = Path(__file__).resolve().parents[2]
    data_dir = Path(output_dir) if output_dir is not None else project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(seed=42)
    timestamp = np.arange(0, duration_seconds + 1, 1, dtype=float)

    speed = 16.0 + 2.5 * np.sin(timestamp / 35.0) + rng.normal(0.0, 0.35, size=len(timestamp))
    speed = np.clip(speed, 0.0, None)
    ax = rng.normal(0.0, 0.35, size=len(timestamp))
    ay = rng.normal(0.0, 0.30, size=len(timestamp))
    yaw_rate = rng.normal(0.0, 0.04, size=len(timestamp))
    steering_angle = rng.normal(0.0, 2.0, size=len(timestamp))

    # Artificial events for deterministic rule checks.
    ax[95:99] = [-3.2, -3.8, -3.5, -3.1]
    speed[95:99] = np.maximum(speed[95:99] - np.array([1.5, 3.0, 4.5, 5.5]), 0.0)
    ax[175:178] = [2.7, 3.0, 2.8]
    ay[135:139] = [2.1, 2.4, 2.2, 2.05]
    yaw_rate[220:223] = [0.38, 0.43, 0.39]
    steering_angle[135:139] = [10.0, 12.0, 11.5, 9.5]

    vehicle_df = pd.DataFrame(
        {
            "timestamp": timestamp,
            "speed": speed.round(3),
            "ax": ax.round(3),
            "ay": ay.round(3),
            "yaw_rate": yaw_rate.round(4),
            "steering_angle": steering_angle.round(3),
            "automation_status": "manual",
            "road_type": "mixed",
        }
    )

    baseline_hr = 72.0
    heart_rate = baseline_hr + 2.0 * np.sin(timestamp / 45.0) + rng.normal(0.0, 1.2, size=len(timestamp))
    heart_rate[95:115] += np.linspace(8.0, 15.0, 20)
    heart_rate[135:155] += np.linspace(6.0, 13.0, 20)
    heart_rate[220:240] += np.linspace(5.0, 12.0, 20)
    rr_interval = 60.0 / np.clip(heart_rate, 45.0, 180.0)

    heart_rate_df = pd.DataFrame(
        {
            "timestamp": timestamp,
            "heart_rate": heart_rate.round(2),
            "rr_interval": rr_interval.round(4),
        }
    )

    vehicle_path = data_dir / "sample_vehicle_log.csv"
    heart_rate_path = data_dir / "sample_heart_rate.csv"
    vehicle_df.to_csv(vehicle_path, index=False)
    heart_rate_df.to_csv(heart_rate_path, index=False)

    return vehicle_path, heart_rate_path


if __name__ == "__main__":
    vehicle_csv, heart_rate_csv = generate_sample_data()
    print(f"Wrote {vehicle_csv}")
    print(f"Wrote {heart_rate_csv}")
