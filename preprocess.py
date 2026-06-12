#!/usr/bin/env python3
"""
Extract per-timestep neuron metrics from monitors/ into a compact binary file.

Output: public/<metric>.npy  — float32 array of shape (n_steps, n_neurons)
        public/sim-meta.json — metadata (steps list, neuron count, metric names)

Column indices in the monitor CSVs (0-based, semicolon-separated, no header):
  0  step
  1  fired
  2  fired_fraction
  3  activity
  4  dampening
  5  current_calcium
  6  target_calcium
  7  synaptic_input
  8  background_input
  9  grown_axons
  10 connected_axons
  11 grown_dendrites
  12 connected_dendrites
"""

import argparse
import json
import os
from pathlib import Path

import numpy as np
from tqdm import tqdm

MONITORS_DIR = Path("public/monitors")
OUTPUT_DIR = Path("public")

COLUMN_MAP = {
    "activity": 3,
    "fired": 1,
    "fired_fraction": 2,
    "dampening": 4,
    "current_calcium": 5,
    "grown_axons": 9,
    "connected_axons": 10,
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Preprocess neuron monitor CSVs into per-metric npy arrays."
    )
    p.add_argument(
        "--metrics",
        nargs="+",
        default=["activity"],
        choices=list(COLUMN_MAP.keys()),
        help="Metrics to extract (default: activity)",
    )
    p.add_argument(
        "--steps",
        type=int,
        default=400,
        help="Number of simulation steps to extract (default: 400, max 10000)",
    )
    p.add_argument("--monitors-dir", type=Path, default=MONITORS_DIR)
    p.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    return p.parse_args()


def main() -> None:
    args = parse_args()
    monitors_dir: Path = args.monitors_dir
    output_dir: Path = args.output_dir
    n_steps: int = min(args.steps, 10000)
    metrics: list[str] = args.metrics

    # Discover neuron IDs from filenames (rank 0 only: 0_<neuron_id>.csv)
    csv_files = sorted(
        monitors_dir.glob("0_*.csv"), key=lambda p: int(p.stem.split("_")[1])
    )
    n_neurons = len(csv_files)
    print(
        f"Found {n_neurons} neurons, extracting {n_steps} steps for metrics: {metrics}"
    )

    # Allocate output arrays: one per metric, shape (n_steps, n_neurons)
    arrays: dict[str, np.ndarray] = {
        m: np.full((n_steps, n_neurons), np.nan, dtype=np.float32) for m in metrics
    }
    col_indices = [COLUMN_MAP[m] for m in metrics]

    steps_recorded: list[int] | None = None

    for neuron_idx, csv_path in enumerate(tqdm(csv_files, unit="neuron")):
        neuron_id = int(csv_path.stem.split("_")[1])
        rows_read = 0
        with open(csv_path) as f:
            for line in f:
                if rows_read >= n_steps:
                    break
                parts = line.rstrip("\n").split(";")
                if neuron_idx == 0:
                    if steps_recorded is None:
                        steps_recorded = []
                    steps_recorded.append(int(parts[0]))
                for m_idx, col in enumerate(col_indices):
                    arrays[metrics[m_idx]][rows_read, neuron_idx] = float(parts[col])
                rows_read += 1

    # Write arrays
    output_dir.mkdir(parents=True, exist_ok=True)
    for metric, arr in arrays.items():
        out_path = output_dir / f"sim-{metric}.npy"
        np.save(out_path, arr)
        print(f"Saved {out_path}  {arr.shape}  {arr.nbytes / 1e6:.1f} MB")

    # Write metadata
    meta = {
        "n_steps": n_steps,
        "n_neurons": n_neurons,
        "steps": steps_recorded,
        "metrics": metrics,
        "neuron_ids": [int(p.stem.split("_")[1]) for p in csv_files],
    }
    meta_path = output_dir / "sim-meta.json"
    with open(meta_path, "w") as f:
        json.dump(meta, f)
    print(f"Saved {meta_path}")


if __name__ == "__main__":
    main()
