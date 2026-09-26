from pathlib import Path
import json

from .config import load_config
from .network import build_network
from .simulator import generate_ground_truth
from .sensors import generate_virtual_sensor_data
from .validation import save_validation_report


ROOT = Path(__file__).resolve().parents[1]


def main():
    config_path = ROOT / "configs" / "config.yaml"
    if not config_path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {config_path}\n"
            "Run this command from the project directory, or check that "
            "configs/config.yaml exists."
        )

    cfg = load_config(config_path)

    raw = ROOT / "data" / "raw"
    processed = ROOT / "data" / "processed"
    raw.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)

    print("Building virtual water distribution network...")
    network = build_network(cfg)

    network.nodes.to_csv(processed / "network_nodes.csv", index=False)
    network.edges.to_csv(processed / "network_edges.csv", index=False)

    print(
        f"Network created: {len(network.nodes)} nodes, "
        f"{len(network.edges)} pipes"
    )

    print("Generating ground-truth simulation data...")
    ground_truth = generate_ground_truth(network, cfg)
    ground_truth.to_csv(raw / "ground_truth.csv", index=False)

    print("Generating virtual sensor observations...")
    sensor_data = generate_virtual_sensor_data(ground_truth, cfg)
    sensor_data.to_csv(raw / "virtual_sensor_data.csv", index=False)

    print("Validating declared measurement ranges...")
    report = save_validation_report(
        ground_truth,
        sensor_data,
        cfg,
        processed / "validation_report.json",
    )

    # Remove the raw ground-truth columns from the Phase-2-facing dataset
    # only if desired later; for experiment we retain both so experiments are auditable.
    sensor_data.to_csv(
        processed / "validated_sensor_data.csv",
        index=False,
    )

    summary = {
        "project": "Computational Water Quality Management",
        "nodes": int(len(network.nodes)),
        "pipes": int(len(network.edges)),
        "records": int(len(ground_truth)),
        "validation_passed": bool(
            report["ground_truth"]["overall_pass"]
            and report["virtual_sensor"]["overall_pass"]
        ),
        "outputs": [
            "network_nodes.csv",
            "network_edges.csv",
            "ground_truth.csv",
            "virtual_sensor_data.csv",
            "validated_sensor_data.csv",
            "validation_report.json",
        ],
    }

    (processed / "run_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print("\nexperiment complete.")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
