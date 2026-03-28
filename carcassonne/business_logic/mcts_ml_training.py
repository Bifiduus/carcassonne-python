"""Utilities to train a Keras model for MCTS child selection.

The dataset is expected to come from played games and contain rows with:
- ``features``: list[float]
- ``target``: float (e.g., rollout reward or win probability)

Supported input formats:
- JSON list file: ``[{"features": [...], "target": ...}, ...]``
- JSON Lines file: one JSON object per line with the same keys
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_MCTS_ML_DIR = Path(__file__).resolve().parents[1] / "datas" / "mcts_ml"
DEFAULT_OUTPUT_MODEL_PATH = DEFAULT_MCTS_ML_DIR / "mcts_selection.keras"


def _load_samples(dataset_path: str) -> tuple[list[list[float]], list[float]]:
    path = Path(dataset_path)
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        raise ValueError("Dataset is empty")

    if text.startswith("["):
        rows = json.loads(text)
    else:
        rows = [json.loads(line) for line in text.splitlines() if line.strip()]

    features: list[list[float]] = []
    targets: list[float] = []
    for row in rows:
        row_features = row.get("features")
        row_target = row.get("target")
        if not isinstance(row_features, list) or row_target is None:
            continue
        features.append([float(value) for value in row_features])
        targets.append(float(row_target))

    if not features:
        raise ValueError("No valid samples in dataset")

    return features, targets


def train_mcts_selection_model(
    dataset_path: str,
    output_path: str,
    epochs: int = 30,
    batch_size: int = 32,
) -> None:
    """Train and save a compact Keras regressor for MCTS selection."""
    import numpy as np
    from keras import layers
    from keras.models import Sequential

    x_train, y_train = _load_samples(dataset_path)
    x_train_np = np.asarray(x_train, dtype="float32")
    y_train_np = np.asarray(y_train, dtype="float32")
    input_dim = int(x_train_np.shape[1])

    model = Sequential(
        [
            layers.Input(shape=(input_dim,)),
            layers.Dense(32, activation="relu"),
            layers.Dense(16, activation="relu"),
            layers.Dense(1, activation="linear"),
        ]
    )

    model.compile(optimizer="adam", loss="mse", metrics=["mae"])
    model.fit(
        x_train_np,
        y_train_np,
        epochs=max(1, int(epochs)),
        batch_size=max(1, int(batch_size)),
        verbose=0,
    )
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    model.save(str(output))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a Keras model for Carcassonne MCTS ML selection."
    )
    parser.add_argument("dataset", help="Path to JSON/JSONL dataset")
    parser.add_argument(
        "output",
        nargs="?",
        default=str(DEFAULT_OUTPUT_MODEL_PATH),
        help=(
            "Path to output .keras model "
            f"(default: {DEFAULT_OUTPUT_MODEL_PATH})"
        ),
    )
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch-size", type=int, default=32)
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    train_mcts_selection_model(
        dataset_path=args.dataset,
        output_path=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
    )
    print(f"Model saved to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
