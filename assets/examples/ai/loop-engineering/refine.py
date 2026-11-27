import hashlib

TESTS = [(2024, True), (2023, False),
         (1900, False), (2000, True)]


def verify(src):
    """검증기: 코드를 실행하고 실패한 테스트를 돌려준다"""
    env = {}
    exec(src, env)
    f = env["is_leap"]
    return [y for y, want in TESTS if f(y) != want]


V1 = "def is_leap(y): return y % 4 == 0"
V2 = ("def is_leap(y):\n"
      "    return y % 4 == 0 and y % 100 != 0")
V3 = ("def is_leap(y):\n"
      "    return (y % 4 == 0 and y % 100 != 0)"
      " or y % 400 == 0")


def converging(src, failed):
    # 실패 목록을 보고 고치는 가짜 수정자
    if 1900 in failed:
        return V2
    if 2000 in failed:
        return V3
    return src


def oscillating(src, failed):
    # 한 실패를 고치면 다른 실패가 생기는 수정자
    return V2 if src == V1 else V1


def refine(draft, revise, max_rounds=5):
    src, seen = draft, set()
    for r in range(1, max_rounds + 1):
        failed = verify(src)
        key = hashlib.sha1(src.encode()).hexdigest()
        print(f"  round {r}: failed={failed}"
              f" id={key[:7]}")
        if not failed:
            return "pass", r
        if key in seen:
            # 같은 코드가 다시 나옴: 더 돌아도 소용없다
            return "oscillation", r
        seen.add(key)
        src = revise(src, failed)
    return "max_rounds", max_rounds


for name, rev in [("converging", converging),
                  ("oscillating", oscillating)]:
    print(f"[{name}]")
    print("  ->", refine(V1, rev))
