import json
from pathlib import Path
from typing import Union

import pandas as pd


RANGE_TO_COLUMN = {
    "flow_m3h": "flow_m3h",
    "pressure_bar": "pressure_bar",
    "chlorine_mg_l": "chlorine_mg_l",
    "ph": "ph",
    "turbidity_ntu": "turbidity_ntu",
    "temperature_c": "temperature_c",
}


def validate_ranges(
    df: pd.DataFrame,
    cfg: dict,
    value_prefix: str = "",
) -> dict:
    report = {}
    all_pass = True

    for range_name, column in RANGE_TO_COLUMN.items():
        actual_column = f"{value_prefix}{column}" if value_prefix else column
        low = cfg["ranges"][range_name]["min"]
        high = cfg["ranges"][range_name]["max"]

        series = df[actual_column].dropna()
        violations = ((series < low) | (series > high)).sum()

        result = {
            "min_allowed": low,
            "max_allowed": high,
            "observed_min": None if series.empty else float(series.min()),
            "observed_max": None if series.empty else float(series.max()),
            "violations": int(violations),
            "pass": bool(violations == 0),
        }

        report[actual_column] = result
        all_pass = all_pass and result["pass"]

    report["overall_pass"] = bool(all_pass)
    return report


def save_validation_report(
    ground_truth: pd.DataFrame,
    sensor_data: pd.DataFrame,
    cfg: dict,
    output_path: Union[str, Path],
):
    report = {
        "ground_truth": validate_ranges(ground_truth, cfg),
        "virtual_sensor": validate_ranges(sensor_data, cfg, "sensor_"),
    }

    output_path = Path(output_path)
    output_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    return report
