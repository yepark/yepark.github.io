import numpy as np

def cosine_similarity(a: list[float], b: list[float]) -> float:
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# 간단한 2차원 예시
apple  = [0.9, 0.1]
pear   = [0.8, 0.2]
car    = [-0.3, 0.9]

print(cosine_similarity(apple, pear))  # 0.98 — 가깝다
print(cosine_similarity(apple, car))   # 0.04 — 멀다

def dot_product(a: list[float], b: list[float]) -> float:
    return float(np.dot(np.array(a), np.array(b)))
