import json, pathlib, sys
from react_loop import run, POLICIES, scripted, A

GOLDEN = pathlib.Path("golden.json")


def summarize(policy):
    reason, s = run(policy, "A-100 배송 상태")
    return [reason] + [n for _, n, _ in s.trace]


now = {k: summarize(p) for k, p in POLICIES.items()}
if not GOLDEN.exists():
    GOLDEN.write_text(json.dumps(now, indent=1))
    print("golden.json 저장")
    sys.exit()

golden = json.loads(GOLDEN.read_text())
bad = [k for k in golden if golden[k] != now[k]]
print("골든 트레이스 비교:", "PASS" if not bad
      else f"FAIL {bad}")

# 정책을 일부러 바꿔서 테스트가 잡아내는지 확인
mutant = scripted(("get_eta", A), ("get_eta", A),
                  ("get_order", A), ("finish", {}))
got = summarize(mutant)
print("기대:", golden["good"])
print("실제:", got)
