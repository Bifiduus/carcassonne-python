from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace

import pytest

import carcassonne.business_logic.mcts_ml_training as training_module


def test_load_samples_rejects_empty_and_invalid_datasets(tmp_path) -> None:
    empty_file = tmp_path / "empty.json"
    empty_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="Dataset is empty"):
        training_module._load_samples(str(empty_file))

    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text(
        '[{"features": "bad", "target": 1}, {"features": [1, 2]}]',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="No valid samples in dataset"):
        training_module._load_samples(str(invalid_file))


def test_load_samples_supports_json_list_and_json_lines(tmp_path) -> None:
    json_file = tmp_path / "samples.json"
    json_file.write_text(
        '[{"features": [1, "2"], "target": "3"}, {"features": [4], "target": 5}]',
        encoding="utf-8",
    )

    jsonl_file = tmp_path / "samples.jsonl"
    jsonl_file.write_text(
        '\n'.join(
            [
                '{"features": [1, 2], "target": 3}',
                '{"features": [4.5], "target": 6}',
            ]
        ),
        encoding="utf-8",
    )

    assert training_module._load_samples(str(json_file)) == (
        [[1.0, 2.0], [4.0]],
        [3.0, 5.0],
    )
    assert training_module._load_samples(str(jsonl_file)) == (
        [[1.0, 2.0], [4.5]],
        [3.0, 6.0],
    )


def test_train_mcts_selection_model_trains_and_saves_with_fake_numpy_and_keras(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    dataset_path = tmp_path / "dataset.json"
    dataset_path.write_text(
        '[{"features": [1, 2], "target": 3}]',
        encoding="utf-8",
    )
    output_path = tmp_path / "models" / "mcts.keras"

    class FakeArray:
        def __init__(self, rows):
            self.rows = rows
            width = len(rows[0]) if rows and isinstance(rows[0], list) else 1
            self.shape = (len(rows), width)

    fake_numpy = ModuleType("numpy")
    fake_numpy.asarray = lambda values, dtype=None: FakeArray(values)

    fake_layers = ModuleType("keras.layers")
    fake_layers.Input = lambda shape: ("Input", shape)
    fake_layers.Dense = lambda units, activation: (
        "Dense",
        units,
        activation,
    )

    class FakeSequential:
        last_instance = None

        def __init__(self, layers):
            self.layers = layers
            self.compile_kwargs = None
            self.fit_kwargs = None
            self.saved_path = None
            FakeSequential.last_instance = self

        def compile(self, **kwargs):
            self.compile_kwargs = kwargs

        def fit(self, x_train, y_train, **kwargs):
            self.fit_kwargs = {
                "x_train": x_train,
                "y_train": y_train,
                **kwargs,
            }

        def save(self, output):
            self.saved_path = output

    fake_models = ModuleType("keras.models")
    fake_models.Sequential = FakeSequential

    fake_keras = ModuleType("keras")
    fake_keras.layers = fake_layers

    monkeypatch.setitem(sys.modules, "numpy", fake_numpy)
    monkeypatch.setitem(sys.modules, "keras", fake_keras)
    monkeypatch.setitem(sys.modules, "keras.models", fake_models)

    training_module.train_mcts_selection_model(
        str(dataset_path),
        str(output_path),
        epochs=0,
        batch_size=0,
    )

    model = FakeSequential.last_instance
    assert model is not None
    assert model.compile_kwargs == {
        "optimizer": "adam",
        "loss": "mse",
        "metrics": ["mae"],
    }
    assert model.fit_kwargs["epochs"] == 1
    assert model.fit_kwargs["batch_size"] == 1
    assert output_path.parent.exists() is True
    assert model.saved_path == str(output_path)


def test_parse_args_and_main_use_expected_defaults(
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "mcts_ml_training.py",
            "dataset.json",
            "output.keras",
            "--epochs",
            "12",
            "--batch-size",
            "7",
        ],
    )
    args = training_module._parse_args()
    assert args.dataset == "dataset.json"
    assert args.output == "output.keras"
    assert args.epochs == 12
    assert args.batch_size == 7

    monkeypatch.setattr(
        training_module,
        "_parse_args",
        lambda: SimpleNamespace(
            dataset="data.json",
            output="trained.keras",
            epochs=2,
            batch_size=4,
        ),
    )
    train_calls = []
    monkeypatch.setattr(
        training_module,
        "train_mcts_selection_model",
        lambda **kwargs: train_calls.append(kwargs),
    )

    assert training_module.main() == 0
    assert train_calls == [
        {
            "dataset_path": "data.json",
            "output_path": "trained.keras",
            "epochs": 2,
            "batch_size": 4,
        }
    ]
    assert "Model saved to trained.keras" in capsys.readouterr().out
