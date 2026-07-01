from pathlib import Path

import pandas as pd


def _load_csv(path: str | Path, expected_name: str) -> pd.DataFrame:
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"{expected_name} file not found: {csv_path}")
    if not csv_path.is_file():
        raise ValueError(f"{expected_name} path is not a file: {csv_path}")

    try:
        return pd.read_csv(csv_path)
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"{expected_name} is empty or has no readable columns: {csv_path}") from exc
    except pd.errors.ParserError as exc:
        raise ValueError(f"{expected_name} is malformed and could not be parsed: {csv_path}") from exc
    except UnicodeDecodeError as exc:
        raise ValueError(f"{expected_name} could not be decoded as text CSV: {csv_path}") from exc


def load_vehicle_log(path: str | Path) -> pd.DataFrame:
    """Load a vehicle log CSV into a pandas DataFrame."""
    return _load_csv(path, "vehicle_log.csv")


def load_heart_rate(path: str | Path) -> pd.DataFrame:
    """Load a heart rate CSV into a pandas DataFrame."""
    return _load_csv(path, "heart_rate.csv")
