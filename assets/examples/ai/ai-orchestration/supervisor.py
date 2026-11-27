# 감독자(supervisor) 방식: 감독자가 작업자를 도구처럼
# 부르고, 결과를 받아 다음 일을 직접 정한다.
# 작업자는 모두 가짜(규칙 함수)다.
MSG = ("주문 A-1001 키보드가 안 켜져요. 환불해 주세요."
       " 내일 출국이라 오늘 안에 답이 필요해요.")


def billing_tool(order):
    return {"order": order, "paid_by": "card"}


def refund_tool(order, paid_by):
    return {"refund_id": "R-77", "eta_days": 3}


def supervisor(msg):
    log = []
    # 1) 감독자가 직접 필요한 정보를 뽑는다
    order = "A-1001"
    urgent = "오늘" in msg
    # 2) 작업자를 차례로 부르고 결과는 요약만 받는다
    pay = billing_tool(order)
    log.append(("billing_tool", pay))
    ref = refund_tool(order, pay["paid_by"])
    log.append(("refund_tool", ref))
    # 3) 제어권은 계속 감독자에게 있다
    for name, out in log:
        print(f"  supervisor <- {name}: {out}")
    note = " 오늘 안 처리 요청 표시" if urgent else ""
    return (f"{order} 환불 {ref['refund_id']} 접수,"
            f" {ref['eta_days']}일 소요.{note}")


print("user:", MSG)
print("  final:", supervisor(MSG))
