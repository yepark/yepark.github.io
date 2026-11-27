from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer


class S(TypedDict, total=False):
    n: int
    msg: str


def step1(state: S):
    w = get_stream_writer()
    w({"진행": "1/2 계산 중"})
    return {"n": state["n"] * 10}


def step2(state: S):
    return {"msg": f"결과 {state['n']}"}


g = StateGraph(S)
g.add_node("step1", step1)
g.add_node("step2", step2)
g.add_edge(START, "step1")
g.add_edge("step1", "step2")
g.add_edge("step2", END)
app = g.compile()

for mode in ["values", "updates", "custom"]:
    print(f"--- {mode}")
    for c in app.stream({"n": 4}, stream_mode=mode):
        print(c)

print("--- 여러 모드 (v1)")
for c in app.stream({"n": 4},
                    stream_mode=["updates", "custom"]):
    print(c)

print("--- v2")
for c in app.stream({"n": 4}, stream_mode="updates",
                    version="v2"):
    print(c)

print("--- debug (type만)")
for c in app.stream({"n": 4}, stream_mode="debug"):
    print(c["step"], c["type"], c["payload"]["name"]
          if "name" in c["payload"] else "")
