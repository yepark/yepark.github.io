from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

PROVIDER = {}   # 가짜 결제사: 멱등성 키 -> 처리 결과


def refund_api(key: str, amount: int):
    if key in PROVIDER:
        return f"중복 요청 무시({key})"
    PROVIDER[key] = amount
    return f"환불 {amount}원 처리({key})"


class State(TypedDict, total=False):
    order_id: str
    amount: int
    decision: str
    receipt: str


def draft(state: State):
    return {"amount": state.get("amount", 30000)}


def approve(state: State):
    print("  [approve 노드 시작]")
    answer = interrupt({"order": state["order_id"],
                        "amount": state["amount"]})
    return {"decision": answer}


def after_approve(state: State) -> Literal[
        "execute", "__end__"]:
    if state["decision"] == "approved":
        return "execute"
    return END


def execute(state: State):
    key = f"refund:{state['order_id']}:{state['amount']}"
    return {"receipt": refund_api(key, state["amount"])}


b = StateGraph(State)
b.add_node("draft", draft)
b.add_node("approve", approve)
b.add_node("execute", execute)
b.add_edge(START, "draft")
b.add_edge("draft", "approve")
b.add_conditional_edges("approve", after_approve)
b.add_edge("execute", END)
app = b.compile(checkpointer=InMemorySaver())
cfg = {"configurable": {"thread_id": "order-77"}}

print("1) 첫 실행")
out = app.invoke({"order_id": "A77"}, cfg)
print("  interrupt:", out["__interrupt__"][0].value)
print("  next:", app.get_state(cfg).next)

print("2) 사람이 승인하고 재개")
out = app.invoke(Command(resume="approved"), cfg)
print("  receipt:", out["receipt"])

print("3) 상태 기록 (최신이 먼저)")
history = list(app.get_state_history(cfg))
for s in history:
    print(f"  step={s.metadata['step']:>2}",
          "next=", s.next)

print("4) execute 직전부터 다시 실행 (replay)")
before = next(s for s in history
              if s.next == ("execute",))
out = app.invoke(None, before.config)
print("  receipt:", out["receipt"])

print("5) 승인 직전에서 금액을 바꿔 분기 (fork)")
pre = next(s for s in history
           if s.next == ("approve",))
fork = app.update_state(pre.config,
                        {"amount": 50000},
                        as_node="draft")
out = app.invoke(None, fork)
print("  interrupt:", out["__interrupt__"][0].value)
