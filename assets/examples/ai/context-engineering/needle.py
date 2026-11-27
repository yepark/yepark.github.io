"""정답 한 줄(needle)의 위치와 질문 위치를 바꿔 가며 로컬 모델의 정답률을 잰다."""
import random
import sys
import time

from mlx_lm import generate, load

MODEL = "mlx-community/Qwen2.5-3B-Instruct-4bit"
N_LINES = int(sys.argv[1]) if len(sys.argv) > 1 else 120
TRIALS = int(sys.argv[2]) if len(sys.argv) > 2 else 12
POSITIONS = [0.0, 0.25, 0.5, 0.75, 1.0]

model, tokenizer = load(MODEL)


def make_case(seed: int):
    rng = random.Random(seed)
    keys = [f"{rng.getrandbits(32):08x}" for _ in range(N_LINES)]
    vals = [f"{rng.randrange(100000, 999999)}" for _ in range(N_LINES)]
    target = rng.randrange(N_LINES)
    return keys, vals, target


def build(keys, vals, target, pos, query_last):
    # target 줄을 원하는 위치로 옮긴다
    order = [i for i in range(N_LINES) if i != target]
    order.insert(round(pos * (N_LINES - 1)), target)
    lines = "\n".join(f"Employee {keys[i]} locker code: {vals[i]}" for i in order)
    q = f"What is the locker code of employee {keys[target]}? Answer with the 6-digit code only."
    body = f"<records>\n{lines}\n</records>"
    content = f"{body}\n\n{q}" if query_last else f"{q}\n\n{body}"
    msgs = [{"role": "user", "content": content}]
    return tokenizer.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)


start = time.time()
results = {}
n_tokens = None
for query_last in (True, False):
    for pos in POSITIONS:
        ok = 0
        for t in range(TRIALS):
            keys, vals, target = make_case(1000 + t)
            prompt = build(keys, vals, target, pos, query_last)
            if n_tokens is None:
                n_tokens = len(tokenizer.encode(prompt))
            out = generate(model, tokenizer, prompt=prompt, max_tokens=10)
            ok += vals[target] in out
        results[(query_last, pos)] = ok
        print(f"query_last={query_last!s:5} pos={pos:.2f} correct={ok}/{TRIALS}", flush=True)

print(f"model={MODEL} lines={N_LINES} prompt_tokens~{n_tokens} trials={TRIALS} greedy max_tokens=10")
print(f"elapsed {time.time() - start:.0f}s")
