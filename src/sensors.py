import numpy as np
import pandas as pd


MEASUREMENT_COLUMNS = [
    "flow_m3h",
    "pressure_bar",
    "chlorine_mg_l",
    "ph",
    "turbidity_ntu",
    "temperature_c",
]


def generate_virtual_sensor_data(
    ground_truth: pd.DataFrame,
    cfg: dict,
) -> pd.DataFrame:
    rng = np.random.default_rng(cfg["seed"] + 100)

    out = ground_truth.copy()

    # Preserve ground truth for evaluation while creating virtual observations.
    for col in MEASUREMENT_COLUMNS:
        fraction = cfg["sensor"]["noise_std_fraction"][col]
        std = max(
            out[col].abs().median() * fraction,
            1e-6,
        )
        out[f"sensor_{col}"] = out[col] + rng.normal(0, std, len(out))

    out["sensor_status"] = "NORMAL"

    # Missing observations.
    missing_p = cfg["sensor"]["missing_probability"]
    missing_mask = rng.random(len(out)) < missing_p

    for col in MEASUREMENT_COLUMNS:
        out.loc[missing_mask, f"sensor_{col}"] = np.nan

    out.loc[missing_mask, "sensor_status"] = "MISSING"

    # Controlled outliers. We create them from the ground truth and then
    # validate/clamp them later against the declared measurement ranges.
    outlier_p = cfg["sensor"]["outlier_probability"]
    candidate = rng.random(len(out)) < outlier_p
    candidate &= ~missing_mask

    multiplier = cfg["sensor"]["outlier_multiplier"]

    for col in MEASUREMENT_COLUMNS:
        idx = np.where(candidate)[0]
        if len(idx):
            values = out.iloc[idx][f"sensor_{col}"].to_numpy()
            center = out.iloc[idx][col].to_numpy()
            out.iloc[idx, out.columns.get_loc(f"sensor_{col}")] = (
                center + (values - center) * multiplier
            )

    out.loc[candidate, "sensor_status"] = "OUTLIER"

    # The synthetic observations must remain inside the original measurement
    # ranges. Outliers therefore represent unusual but physically bounded
    # observations rather than impossible values.
    for range_name, col in {
        "flow_m3h": "flow_m3h",
        "pressure_bar": "pressure_bar",
        "chlorine_mg_l": "chlorine_mg_l",
        "ph": "ph",
        "turbidity_ntu": "turbidity_ntu",
        "temperature_c": "temperature_c",
    }.items():
        low = cfg["ranges"][range_name]["min"]
        high = cfg["ranges"][range_name]["max"]
        sensor_col = f"sensor_{col}"
        out[sensor_col] = out[sensor_col].clip(lower=low, upper=high)

    return out
