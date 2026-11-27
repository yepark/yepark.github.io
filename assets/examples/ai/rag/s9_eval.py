from store import build

tests = [
    ("결제하고 10일 지났는데 환불되나요?", "refund.md"),
    ("연간 플랜 환불 기간", "refund.md"),
    ("프로 플랜 가격", "pricing.md"),
    ("무료로 프로젝트 몇 개?", "pricing.md"),
    ("주말에 문의하는 방법", "support.md"),
    ("E-4012 오류가 떴어요", "error-4012.md"),
    ("카드 한도 초과 오류", "error-4013.md"),
]

for size in (60, 200):
    store = build(size, 10)
    for k in (1, 2):
        miss = []
        for q, want in tests:
            got = store.similarity_search(q, k=k)
            if want not in [d.metadata["source"] for d in got]:
                miss.append(q)
        hit = len(tests) - len(miss)
        print(f"chunk={size:3} k={k} "
              f"hit={hit}/{len(tests)} miss={miss}")
