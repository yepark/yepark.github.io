"""Reproduce the MLX articles on Apple silicon; prints results as JSON."""
import gc
import json
import math
import platform
import statistics
import time
from importlib.metadata import version

import mlx.core as mx


def validate_arrays():
    x = mx.array([[1, 2, 3], [4, 5, 6]], dtype=mx.float32)
    shifted = x + mx.array([10, 20, 30], dtype=mx.float32)
    normalized = x - mx.mean(x, axis=1, keepdims=True)
    product = x @ x.T
    mx.eval(shifted, normalized, product)
    assert shifted.tolist() == [[11, 22, 33], [14, 25, 36]]
    assert normalized.tolist() == [[-1, 0, 1], [-1, 0, 1]]
    assert product.tolist() == [[14, 32], [32, 77]]
    assert mx.sum(x, axis=0).tolist() == [5, 7, 9]
    assert mx.sum(x, axis=1).tolist() == [6, 15]

    sequence = mx.arange(6).reshape(2, 3)
    assert sequence.reshape(3, 2).tolist() == [[0, 1], [2, 3], [4, 5]]
    transposed_add = sequence.T + mx.full((3, 2), 10)
    assert transposed_add.tolist() == [[10, 13], [11, 14], [12, 15]]

    prediction = mx.array([[1.0], [2.0]])
    target = mx.array([1.0, 2.0])
    wrong_errors = prediction - target
    assert wrong_errors.shape == (2, 2)
    wrong_loss = mx.mean(mx.square(wrong_errors)).item()
    correct_loss = mx.mean(mx.square(prediction.squeeze(-1) - target)).item()
    assert wrong_loss == 0.5 and correct_loss == 0.0

    def loss(w):
        return mx.sum(w * w)

    gradient = mx.grad(loss)(mx.array([1.0, -2.0, 3.0]))
    assert gradient.tolist() == [2, -4, 6]
    return {
        "shape": list(x.shape),
        "dtype": str(x.dtype),
        "broadcast": shifted.tolist(),
        "row_centered": normalized.tolist(),
        "matrix_product": product.tolist(),
        "gradient": gradient.tolist(),
        "transposed_add": transposed_add.tolist(),
        "broadcast_loss": {"wrong_shape": list(wrong_errors.shape),
                           "wrong": wrong_loss, "correct": correct_loss},
    }


def benchmark_matmul(device, size=512, warmup=3, repeats=12):
    with mx.stream(device):
        a = mx.random.normal((size, size), dtype=mx.float32)
        b = mx.random.normal((size, size), dtype=mx.float32)
        mx.eval(a, b)
        for _ in range(warmup):
            mx.eval(a @ b)
        graph_ms, completion_ms, total_ms = [], [], []
        for _ in range(repeats):
            start = time.perf_counter()
            out = a @ b  # Construct a new graph for every sample.
            submitted = time.perf_counter()
            mx.eval(out)  # Include completion, not just graph construction.
            end = time.perf_counter()
            graph_ms.append((submitted - start) * 1000)
            completion_ms.append((end - submitted) * 1000)
            total_ms.append((end - start) * 1000)
        start = time.perf_counter()
        mx.eval(out)  # Cached result: not a new matrix multiplication.
        cached_ms = (time.perf_counter() - start) * 1000

    ordered = sorted(total_ms)
    return {
        "device": str(device),
        "shape": [size, size],
        "dtype": "float32",
        "warmup": warmup,
        "repeats": repeats,
        "graph_median_ms": statistics.median(graph_ms),
        "completion_median_ms": statistics.median(completion_ms),
        "total_median_ms": statistics.median(total_ms),
        "total_p95_ms": ordered[math.ceil(0.95 * repeats) - 1],
        "reevaluate_same_output_ms": cached_ms,
    }


def observe_memory():
    gc.collect()
    before = mx.get_active_memory()
    x = mx.ones((1024, 1024), dtype=mx.float32)
    constructed = mx.get_active_memory()
    mx.eval(x)
    evaluated = mx.get_active_memory()
    return {
        "before_bytes": before,
        "after_graph_bytes": constructed,
        "after_eval_bytes": evaluated,
        "logical_array_bytes": x.nbytes,
        "note": "MLX active allocation is not total process memory.",
    }


def compare_devices():
    x = mx.array([[1.0, 2.0], [3.0, 4.0]])
    cpu = mx.matmul(x, x, stream=mx.cpu)
    gpu = mx.matmul(x, x, stream=mx.gpu)
    mx.eval(cpu, gpu)
    assert mx.allclose(cpu, gpu, rtol=1e-5, atol=1e-6).item()
    return {"cpu": cpu.tolist(), "gpu": gpu.tolist()}


if __name__ == "__main__":
    mx.random.seed(7)
    print(json.dumps({
        "environment": {
            "architecture": platform.machine(),
            "macOS": platform.mac_ver()[0],
            "python": platform.python_version(),
            "mlx": version("mlx"),
            "default_device": str(mx.default_device()),
        },
        "arrays": validate_arrays(),
        "device_comparison": compare_devices(),
        "memory": observe_memory(),
        "benchmarks": [benchmark_matmul(mx.cpu), benchmark_matmul(mx.gpu)],
    }, ensure_ascii=False, indent=2))
