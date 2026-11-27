from route import route

CASES = [
    ({"category": "howto"}, "howto"),
    ({"category": "billing"}, "billing"),
    ({"category": "empty"}, "clarify"),
    ({"category": "unknown"}, "clarify"),
    ({"category": "Billing"}, "clarify"),
]

for state, want in CASES:
    got = route(state)
    mark = "ok" if got == want else "FAIL"
    print(f"{mark:4} {state['category']:8} -> {got}")
