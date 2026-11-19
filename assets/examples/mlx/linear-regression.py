"""Learn y = 2x + 1, verify gradients, and round-trip parameters.

Run: uv run --no-project --python 3.12 --with mlx==0.32.4 python linear-regression.py
"""

import json
import platform
import tempfile
from importlib.metadata import version
from pathlib import Path

import mlx.core as mx


def predict(parameters, x):
    return x * parameters[0] + parameters[1]


def loss(parameters, x, y):
    return mx.mean(mx.square(predict(parameters, x) - y))


def main():
    x = mx.array([-2, -1, 0, 1, 2], dtype=mx.float32)
    y = 2 * x + 1
    parameters = mx.array([0, 0], dtype=mx.float32)
    value_and_grad = mx.value_and_grad(loss)
    initial_loss, first_gradient = value_and_grad(parameters, x, y)
    mx.eval(initial_loss, first_gradient)
    assert abs(initial_loss.item() - 9) < 1e-6
    assert mx.allclose(first_gradient, mx.array([-8.0, -2.0])).item()

    history = {}
    for step in range(1, 101):
        _, gradient = value_and_grad(parameters, x, y)
        parameters = parameters - 0.1 * gradient
        mx.eval(parameters)
        if step in (1, 5, 20, 100):
            history[step] = round(loss(parameters, x, y).item(), 8)

    final_loss = loss(parameters, x, y).item()
    assert final_loss < 1e-10
    assert mx.allclose(parameters, mx.array([2.0, 1.0]), atol=1e-5).item()
    held_out_x = mx.array([3.0], dtype=mx.float32)
    held_out_prediction = predict(parameters, held_out_x).item()
    assert abs(held_out_prediction - 7) < 1e-5

    with tempfile.TemporaryDirectory(prefix="mlx-regression-") as folder:
        target = str(Path(folder) / "parameters.npz")
        mx.savez(target, parameters=parameters)
        restored = mx.load(target)["parameters"]
        assert mx.array_equal(restored, parameters).item()

    print(json.dumps({
        "environment": {"python": platform.python_version(), "mlx": version("mlx"),
                        "machine": platform.machine(), "macOS": platform.mac_ver()[0]},
        "initial_loss": initial_loss.item(),
        "first_gradient": first_gradient.tolist(),
        "loss_after_update": history,
        "parameters": [round(v, 6) for v in parameters.tolist()],
        "held_out_prediction": round(held_out_prediction, 6),
        "save_load": "passed",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
