import math
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


def _clip(value, low, high):
    return max(low, min(high, value))


def _scenario(t: int, total_steps: int) -> str:
    # Controlled scenarios for experimentation.
    p = t / max(total_steps - 1, 1)

    if 0.20 <= p < 0.30:
        return "MORNING_DEMAND_PEAK"
    if 0.50 <= p < 0.58:
        return "EVENING_DEMAND_PEAK"
    if 0.70 <= p < 0.76:
        return "PUMP_STRESS"
    if 0.82 <= p < 0.86:
        return "CHLORINE_DECAY_EVENT"
    return "NORMAL"


def generate_ground_truth(network, cfg: dict) -> pd.DataFrame:
    rng = np.random.default_rng(cfg["seed"])

    days = cfg["simulation"]["days"]
    interval = cfg["simulation"]["interval_minutes"]
    steps = int(days * 24 * 60 / interval)

    r = cfg["ranges"]
    start = datetime(2025, 1, 1)

    node_df = network.nodes.copy()
    records = []

    # Fixed node characteristics make the dataset reproducible.
    node_phase = {
        row.node_id: rng.uniform(0, 2 * math.pi)
        for row in node_df.itertuples()
    }

    for step in range(steps):
        timestamp = start + timedelta(minutes=step * interval)
        hour = timestamp.hour + timestamp.minute / 60.0
        scenario = _scenario(step, steps)

        # Demand profile: low overnight, two daily peaks.
        morning = math.exp(-((hour - 8.0) ** 2) / 5.0)
        evening = math.exp(-((hour - 18.5) ** 2) / 7.0)
        daily_factor = 0.55 + 0.65 * morning + 0.75 * evening

        for row in node_df.itertuples():
            if row.node_type == "reservoir":
                continue

            phase = node_phase[row.node_id]

            # Smooth deterministic + stochastic demand component.
            seasonal = 1.0 + 0.08 * math.sin(2 * math.pi * step / (steps / 3))
            local = 1.0 + 0.10 * math.sin(phase + step / 80.0)
            demand = 180.0 * daily_factor * seasonal * local

            if scenario == "MORNING_DEMAND_PEAK":
                demand *= 1.15
            elif scenario == "EVENING_DEMAND_PEAK":
                demand *= 1.20
            elif scenario == "PUMP_STRESS":
                demand *= 1.10

            demand += rng.normal(0, 6.0)
            demand = _clip(demand, 20.0, 500.0)

            # Aggregate flow proxy. Kept within the source-defined 0-1500 m3/h range.
            flow = demand * (1.05 + 0.05 * math.sin(phase))
            flow = _clip(flow, r["flow_m3h"]["min"], r["flow_m3h"]["max"])

            # Elevation affects pressure. The formula is intentionally transparent;
            # experiment is a controlled virtual environment, not a claim of field data.
            pressure = (
                5.8
                - 0.055 * (row.elevation_m - 20.0)
                - 0.0008 * max(flow - 250.0, 0)
                + 0.15 * math.sin(2 * math.pi * hour / 24.0 + phase)
            )

            if scenario == "PUMP_STRESS":
                pressure -= 0.65
            pressure += rng.normal(0, 0.04)
            pressure = _clip(
                pressure,
                r["pressure_bar"]["min"],
                r["pressure_bar"]["max"],
            )

            # Water age proxy increases downstream / with lower flow.
            water_age = _clip(
                1.5 + 0.04 * abs(row.elevation_m - 20) + 800 / max(flow, 20),
                0.1,
                120.0,
            )

            temperature = 24.0 + 3.0 * math.sin(
                2 * math.pi * (step / max(steps, 1)) - 0.8
            )
            temperature += rng.normal(0, 0.15)
            temperature = _clip(
                temperature,
                r["temperature_c"]["min"],
                r["temperature_c"]["max"],
            )

            ph = 7.35 + 0.15 * math.sin(phase + step / 150.0)
            ph += rng.normal(0, 0.025)
            ph = _clip(ph, r["ph"]["min"], r["ph"]["max"])

            # Chlorine decreases with water age and is affected by the event.
            chlorine = (
                0.82
                * math.exp(-0.008 * water_age)
                * (1.0 + 0.04 * math.sin(phase + step / 60))
            )

            if scenario == "CHLORINE_DECAY_EVENT":
                chlorine *= 0.55

            chlorine += rng.normal(0, 0.012)
            chlorine = _clip(
                chlorine,
                r["chlorine_mg_l"]["min"],
                r["chlorine_mg_l"]["max"],
            )

            # Turbidity remains low under normal conditions but rises during
            # the controlled stress event.
            turbidity = 0.45 + 0.10 * abs(math.sin(phase + step / 100))
            if scenario == "CHLORINE_DECAY_EVENT":
                turbidity += 0.25
            turbidity += rng.normal(0, 0.03)
            turbidity = _clip(
                turbidity,
                r["turbidity_ntu"]["min"],
                r["turbidity_ntu"]["max"],
            )

            velocity = flow / 1000.0
            reynolds_proxy = velocity * 100000

            records.append({
                "timestamp": timestamp.isoformat(),
                "node_id": row.node_id,
                "zone": int(row.zone),
                "scenario": scenario,
                "elevation_m": round(row.elevation_m, 4),
                "demand_m3h": round(demand, 4),
                "flow_m3h": round(flow, 4),
                "pressure_bar": round(pressure, 4),
                "water_age_h": round(water_age, 4),
                "temperature_c": round(temperature, 4),
                "ph": round(ph, 4),
                "chlorine_mg_l": round(chlorine, 4),
                "turbidity_ntu": round(turbidity, 4),
                "velocity_proxy": round(velocity, 6),
                "reynolds_proxy": round(reynolds_proxy, 2),
            })

    return pd.DataFrame(records)
