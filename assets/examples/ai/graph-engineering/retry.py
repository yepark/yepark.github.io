from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import RetryPolicy

outbox = []          # 실제로 나간 메일
attempt = {"n": 0}


class State(TypedDict, total=False):
    to: str
    ok: bool


def notify(s: State):
    attempt["n"] += 1
    outbox.append(s["to"])          # 부수 효과 먼저
    if attempt["n"] == 1:
        raise TimeoutError("응답 확인 실패")
    return {"ok": True}


b = StateGraph(State)
b.add_node("notify", notify,
           retry_policy=RetryPolicy(
               max_attempts=3,
               initial_interval=0.01,
               retry_on=TimeoutError))
b.add_edge(START, "notify")
b.add_edge("notify", END)
app = b.compile()

print(app.invoke({"to": "kim@example.com"}))
print("시도:", attempt["n"], "발송함:", outbox)
