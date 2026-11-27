import mlx.core as mx
import mlx.nn as nn

mx.random.seed(0)
layer = nn.Linear(2, 3)
print(layer)
print(layer.weight.shape, layer.bias.shape)

x = mx.array([[0.0, 1.0]])
y = layer(x)
print(y.shape)
manual = x @ layer.weight.T + layer.bias
print(mx.allclose(y, manual).item())
