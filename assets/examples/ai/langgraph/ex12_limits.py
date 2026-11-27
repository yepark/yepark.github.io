from dataclasses import dataclass
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.errors import GraphRecursionError
from langgraph.managed import RemainingSteps
from langgraph.runtime import Runtime


class S(TypedDict):
    tries: int
    left: RemainingSteps   # 남은 단계 수 (자동으로 채워짐)


@dataclass
class Ctx:
    target: int = 99       # 실행마다 바꾸는 설정


def attempt(state: S, runtime: Runtime[Ctx]):
    return {"tries": state["tries"] + 1}


def route(state: S, runtime: Runtime[Ctx]):
    if state["tries"] >= runtime.context.target:
        return "done"
    if state["left"] <= 2:
        return "give_up"
    return "again"


g = StateGraph(S, context_schema=Ctx)
g.add_node("attempt", attempt)
g.add_node("give_up", lambda s: {"tries": -1})
g.add_edge(START, "attempt")
g.add_conditional_edges("attempt", route, {
    "again": "attempt", "done": END,
    "give_up": "give_up"})
g.add_edge("give_up", END)
app = g.compile()

print(app.invoke({"tries": 0}, context={"target": 3}))
print(app.invoke({"tries": 0}, {"recursion_limit": 6},
                 context=Ctx()))
try:
    app.invoke({"tries": 0})   # context를 빠뜨림
except AttributeError as e:
    print("AttributeError:", e)

# 안전장치 없이 돌기만 하는 그래프
g2 = StateGraph(S)
g2.add_node("spin", lambda s: {"tries": s["tries"] + 1})
g2.add_edge(START, "spin")
g2.add_edge("spin", "spin")
try:
    g2.compile().invoke({"tries": 0},
                        {"recursion_limit": 5})
except GraphRecursionError as e:
    print("GraphRecursionError:",
          str(e).splitlines()[0])
