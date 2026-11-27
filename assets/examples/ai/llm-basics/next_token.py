import math
import random
from collections import Counter, defaultdict

corpus = (
    "고양이가 밥을 먹는다. 고양이가 잠을 잔다. 고양이가 밥을 먹는다. "
    "강아지가 밥을 먹는다. 강아지가 공을 쫓는다. 고양이가 공을 쫓는다."
)

# 1. 토큰화: 여기서는 띄어쓰기 단위로 자른다
tokens = corpus.replace(".", " .").split()
print("토큰 수:", len(tokens), "| 앞 6개:", tokens[:6])

# 2. 학습: 각 토큰 다음에 어떤 토큰이 몇 번 왔는지 센다
next_counts = defaultdict(Counter)
for cur, nxt in zip(tokens, tokens[1:]):
    next_counts[cur][nxt] += 1
print("'고양이가' 다음:", dict(next_counts["고양이가"]))

# 3. 다음 토큰 확률: 횟수를 점수로 보고 온도를 적용한 softmax
def probs(word, temperature):
    cands = next_counts[word]
    scores = {w: math.log(c) / temperature for w, c in cands.items()}
    m = max(scores.values())
    exp = {w: math.exp(s - m) for w, s in scores.items()}
    total = sum(exp.values())
    return {w: round(v / total, 2) for w, v in exp.items()}

for t in (0.5, 1.0, 2.0):
    print(f"온도 {t}:", probs("고양이가", t))

# 4. 생성: 한 토큰씩 골라 이어 붙인다
def generate(start, temperature, seed, max_tokens=8):
    rng = random.Random(seed)
    out = [start]
    while len(out) < max_tokens and out[-1] != ".":
        p = probs(out[-1], temperature)
        out.append(rng.choices(list(p), weights=list(p.values()))[0])
    return " ".join(out)

for seed in (1, 2, 3):
    print(f"seed {seed}:", generate("강아지가", 1.0, seed))
