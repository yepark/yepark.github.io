from dataclasses import dataclass, field

# 가짜 도구: 주문 시스템
ORDERS = {"A-100": {"status": "shipped",
                    "eta": "2026-11-29"}}


def get_order(order_id):
    o = ORDERS.get(order_id)
    if o is None:
        return {"error": "not_found"}
    return {"status": o["status"]}


def get_eta(order_id):
    o = ORDERS.get(order_id)
    return {"eta": o["eta"] if o else None}


def search_faq(query):
    return {"hits": []}  # 항상 빈 결과


TOOLS = {"get_order": get_order,
         "get_eta": get_eta,
         "search_faq": search_faq}
REQUIRED = {"status", "eta"}  # 완료 조건


@dataclass
class State:
    goal: str
    step: int = 0
    facts: dict = field(default_factory=dict)
    actions: list = field(default_factory=list)
    stale: int = 0      # 새 사실 없이 지난 횟수
    trace: list = field(default_factory=list)


def check_finish(state):
    missing = REQUIRED - state.facts.keys()
    if missing:
        return f"rejected: missing {sorted(missing)}"
    return None


def run(policy, goal, max_steps=6,
        max_stale=3, max_repeat=3):
    s = State(goal)
    while True:
        # 1) 예산 확인
        if s.step >= max_steps:
            return "max_steps", s
        s.step += 1
        # 2) 결정
        name, args = policy(s)
        s.actions.append((name, args))
        # 3) 행동
        if name == "finish":
            err = check_finish(s)
            if err is None:
                s.trace.append((s.step, name, "ok"))
                return "done", s
            obs = {"error": err}
        else:
            try:
                obs = TOOLS[name](**args)
            except Exception as e:
                # 예외도 관찰로 바꿔 돌려준다
                obs = {"error": repr(e)}
        # 4) 상태 갱신
        new = {k: v for k, v in obs.items()
               if k in REQUIRED and v is not None
               and s.facts.get(k) != v}
        s.facts.update(new)
        s.stale = 0 if new else s.stale + 1
        s.trace.append((s.step, name, obs))
        # 5) 멈출지 판단
        last = s.actions[-max_repeat:]
        if (len(last) == max_repeat
                and len(set(map(str, last))) == 1):
            return "repeated_action", s
        if s.stale >= max_stale:
            return "no_progress", s


def scripted(*plan):
    """정해진 행동을 차례로 내놓는 가짜 정책"""
    def policy(state):
        i = min(state.step - 1, len(plan) - 1)
        return plan[i]
    return policy


A = {"order_id": "A-100"}
B = {"order_id": "B-200"}  # 없는 주문
POLICIES = {
    "good": scripted(("get_order", A),
                     ("get_eta", A),
                     ("finish", {})),
    "premature": scripted(("finish", {}),
                          ("get_order", A),
                          ("get_eta", A),
                          ("finish", {})),
    "stubborn": scripted(("get_eta", B)),
    "wander": scripted(
        ("search_faq", {"query": "배송"}),
        ("search_faq", {"query": "택배"}),
        ("search_faq", {"query": "도착"}),
        ("search_faq", {"query": "언제"})),
}

if __name__ == "__main__":
    for label, pol in POLICIES.items():
        reason, s = run(pol, "A-100 배송 상태")
        print(f"[{label}] -> {reason}"
              f" (steps={s.step})")
        for step, name, obs in s.trace:
            print(f"  {step}. {name:<10} {obs}")
    # max_steps: 한도를 아주 작게
    reason, s = run(POLICIES["good"], "x",
                    max_steps=2)
    print(f"[good, max_steps=2] -> {reason}"
          f" facts={s.facts}")
