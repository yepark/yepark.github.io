import numpy as np
import warnings
warnings.simplefilter("ignore", np.exceptions.RankWarning)

rng = np.random.default_rng(0)
x = np.sort(rng.uniform(0, 1, 20))
y = np.sin(2 * np.pi * x) + rng.normal(0, 0.2, x.size)

idx = rng.permutation(x.size)
train, test = idx[:14], idx[14:]

def mse(coef, i):
    return np.mean((np.polyval(coef, x[i]) - y[i]) ** 2)

for degree in (1, 3, 12):
    coef = np.polyfit(x[train], y[train], degree)
    print(f"degree={degree}  train MSE={mse(coef, train):.3f}  test MSE={mse(coef, test):.3f}")
