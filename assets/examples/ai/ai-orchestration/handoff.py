# 핸드오프 방식: 에이전트가 다음 에이전트에게
# 제어권을 넘긴다. 에이전트는 모두 가짜(규칙 함수)다.
MSG = ("주문 A-1001 키보드가 안 켜져요. 환불해 주세요."
       " 내일 출국이라 오늘 안에 답이 필요해요.")


def triage(ctx):
    # 대화 전체 대신 요약만 넘긴다
    summary = {"intent": "refund", "order": "A-1001",
               "reason": "불량"}
    return ("handoff", "refund", summary)


def refund(ctx):
    if ctx.get("paid_by") is None:
        return ("handoff", "billing", ctx)
    return ("final",
            f"{ctx['order']} 환불 접수 ({ctx['paid_by']})")


def billing(ctx):
    ctx = {**ctx, "paid_by": "card"}
    return ("handoff", "refund", ctx)


def billing_bug(ctx):
    return ("handoff", "refund", ctx)  # 정보를 안 채움


def run(agents, start, ctx, max_hops=4):
    active, hops = start, 0
    while True:
        kind, *rest = agents[active](ctx)
        if kind == "final":
            print(f"  [{active}] final: {rest[0]}")
            return rest[0]
        target, ctx = rest
        hops += 1
        print(f"  hop {hops}: {active} -> {target}"
              f" ctx={ctx}")
        if hops >= max_hops:
            print("  stop: max_hops reached,"
                  " escalate to human")
            return None
        active = target


A = {"triage": triage, "refund": refund,
     "billing": billing}
print("user:", MSG)
print("[정상 흐름]")
run(A, "triage", {"text": MSG})
print("[billing이 정보를 못 채우는 경우]")
run({**A, "billing": billing_bug}, "triage",
    {"text": MSG})
