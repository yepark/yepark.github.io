import operator
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

calls = {"manual": 0, "policy": 0}
broken = {"policy": True}


class State(TypedDict):
    found: Annotated[list[str], operator.add]


def manual(state: State):
    calls["manual"] += 1
    return {"found": ["manual"]}


def policy(state: State):
    calls["policy"] += 1
    if broken["policy"]:
        raise TimeoutError("정책 서버 시간 초과")
    return {"found": ["policy"]}


def write(state: State):
    return {}


b = StateGraph(State)
b.add_node("manual", manual)
b.add_node("policy", policy)
b.add_node("write", write)
b.add_edge(START, "manual")
b.add_edge(START, "policy")
b.add_edge(["manual", "policy"], "write")
b.add_edge("write", END)
app = b.compile(checkpointer=InMemorySaver())
cfg = {"configurable": {"thread_id": "t1"}}

try:
    app.invoke({"found": []}, cfg)
except TimeoutError as e:
    print("1차 실패:", e)
snap = app.get_state(cfg)
print("next:", snap.next)
print("tasks:", [(t.name, t.error is not None)
                 for t in snap.tasks])

broken["policy"] = False        # 서버가 회복됐다
out = app.invoke(None, cfg)     # 같은 thread 재개
print("결과:", out["found"])
print("호출 횟수:", calls)
