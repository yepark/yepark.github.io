import mlx.core as mx
import mlx.nn as nn
import mlx.optimizers as optim
from mlx.utils import tree_flatten

X = mx.array([[0, 0], [0, 1], [1, 0], [1, 1]],
             dtype=mx.float32)
Y = mx.array([[0], [1], [1], [0]], dtype=mx.float32)


def loss_fn(model, x, y):
    return nn.losses.mse_loss(model(x), y)


def train(model, steps=500, lr=0.1):
    mx.eval(model.parameters())
    loss_and_grad = nn.value_and_grad(model, loss_fn)
    opt = optim.SGD(learning_rate=lr)
    for step in range(1, steps + 1):
        loss, grads = loss_and_grad(model, X, Y)
        opt.update(model, grads)
        mx.eval(model.parameters(), opt.state)
        if step in (1, 100, 500):
            print(f"step {step:3d} loss {loss.item():.4f}")
    return model

mx.random.seed(0)
line = train(nn.Linear(2, 1))
print(mx.round(line(X), 2).tolist())

class MLP(nn.Module):
    def __init__(self, hidden):
        super().__init__()
        self.l1 = nn.Linear(2, hidden)
        self.l2 = nn.Linear(hidden, 1)

    def __call__(self, x):
        x = nn.relu(self.l1(x))
        return self.l2(x)

from mlx.utils import tree_map

mx.random.seed(0)
mlp = MLP(8)
print(mlp)
shapes = tree_map(lambda p: p.shape, mlp.parameters())
print(shapes)
n = sum(v.size for _, v in tree_flatten(mlp.parameters()))
print("params", n)

mlp = train(mlp)
print(mx.round(mlp(X), 2).tolist())

mlp.l1.freeze()
names = [k for k, _ in
         tree_flatten(mlp.trainable_parameters())]
print(names)
