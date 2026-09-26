# Reading and Explaining the Results

This guide explains what to look at after running the experiment and how to
describe the results without presenting synthetic data as real-world observations.

## 1. Start with `run_summary.json`

This file is the quickest health check.

Example fields:

- `nodes`: number of virtual network nodes.
- `pipes`: number of virtual pipes.
- `records`: number of generated observations.
- `validation_passed`: whether the generated reference and measurement datasets
  stayed inside the configured ranges.

A successful run should have `validation_passed` set to `true`.

Suggested explanation:

> The computational experiment generated a reproducible distribution network
> and a corresponding time-series dataset. All generated variables were checked
> against their configured operating ranges before the dataset was used for
> further analysis.

Do not describe this as proof that a real distribution network satisfies those
ranges. It only confirms the behaviour of the synthetic experiment.

## 2. Read `validation_report.json`

This is the most important quality-control result.

For every variable it reports:

- minimum allowed value;
- maximum allowed value;
- minimum generated value;
- maximum generated value;
- number of range violations;
- pass/fail status.

For example, if:

```text
chlorine_mg_l
allowed: 0.0–2.5
observed: 0.14–0.86
violations: 0
pass: true
```

the correct interpretation is:

> The generated chlorine observations remained within the configured
> experimental range. No generated value violated the specified bounds.

It does **not** mean that the model has demonstrated regulatory compliance.

## 3. Read `network_nodes.csv`

This describes the virtual network nodes.

Useful columns include:

- `node_id`
- `node_type`
- `zone`
- `elevation_m`

Use this file to understand the spatial structure of the experiment.

## 4. Read `network_edges.csv`

This describes the virtual pipes.

Important columns:

- `pipe_id`
- `from_node`
- `to_node`
- `length_m`
- `diameter_mm`
- `roughness`

This allows later experiments to connect water-quality behaviour to network
topology and pipe characteristics.

## 5. Read `ground_truth.csv`

This is the reference state produced by the simulator.

Important variables:

- `flow_m3h`
- `pressure_bar`
- `water_age_h`
- `temperature_c`
- `ph`
- `chlorine_mg_l`
- `turbidity_ntu`

For modelling experiments, this dataset is useful because the true simulated
state is known. That gives us an objective target against which a predictive
model can be evaluated.

## 6. Read `virtual_sensor_data.csv`

This dataset represents what a measurement system might observe.

For each physical variable there is a corresponding `sensor_` column, for example:

```text
chlorine_mg_l
sensor_chlorine_mg_l
```

The first is the reference value and the second is the measurement-like value.

The `sensor_status` field identifies:

- `NORMAL`
- `MISSING`
- `OUTLIER`

This distinction is important when calculating model performance.

## 7. How to explain the difference between reference and measurement

A useful experiment is:

```text
reference chlorine
        vs
sensor chlorine
```

If the sensor value is close to the reference value, the measurement model has
introduced only a small deviation.

If the difference is larger, it may be due to the configured measurement noise
or a controlled outlier.

For a later ML experiment, the reference value can be treated as the target and
the measurement-like variables as inputs.

## 8. What results are scientifically useful?

The first experiment is primarily a dataset and experimental-environment
validation. The important questions are:

1. Are the network and time series generated reproducibly?
2. Are variables inside their declared ranges?
3. Are the distributions plausible and stable?
4. Are different operating scenarios distinguishable?
5. Does the measurement model introduce controlled imperfections?
6. Is there enough variation for a predictive model to learn meaningful
   relationships?

The strongest scientific results will come later when predictive models are
compared against the known reference state.

## 9. Suggested plots

For analysis, create:

### Time-series plots

Plot pressure, flow and chlorine for one or more representative nodes.

Look for:

- daily demand patterns;
- pressure response to demand;
- chlorine reduction with increasing water age;
- changes during controlled scenarios.

### Distribution plots

Plot histograms of:

- pressure;
- flow;
- chlorine;
- pH;
- turbidity;
- temperature.

Use these to verify that generated data are not concentrated at unrealistic
boundary values.

### Reference vs measurement

Scatter:

```text
reference value
       vs
measurement value
```

A tightly clustered relationship indicates low measurement error.

### Scenario comparison

Compare normal operation with:

- demand peaks;
- pump stress;
- chlorine-decay event.

The purpose is to verify that the scenarios actually produce distinguishable
system behaviour.

## 10. What not to claim

Because the current dataset is synthetic, avoid statements such as:

> "The system accurately predicts real municipal water quality."

Instead say:

> "The computational experiment demonstrates that the proposed modelling
> environment can generate controlled hydraulic and water-quality observations
> within the specified parameter ranges."

Later, once EPANET is integrated, the same distinction should remain:

> EPANET-generated values are simulation results, not field measurements.

This distinction should be preserved throughout the research.
