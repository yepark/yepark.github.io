import operator
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Overwrite


def keep_max(old: int, new: int) -> int:
    return max(old, new)


class State(TypedDict):
    last: str                               # 덮어쓰기
    logs: Annotated[list[str], operator.add]  # 이어 붙이기
    best: Annotated[int, keep_max]          # 직접 만든 규칙


def a(state: State):
    return {"last": "a", "logs": ["a"], "best": 7}


def b(state: State):
    return {"last": "b", "logs": ["b"], "best": 3}


def reset(state: State):
    return {"logs": Overwrite(["reset"])}


g = StateGraph(State)
g.add_node("a", a)
g.add_node("b", b)
g.add_node("reset", reset)
g.add_edge(START, "a")
g.add_edge("a", "b")
g.add_edge("b", END)
app = g.compile()
print(app.invoke({"last": "", "logs": ["start"], "best": 0}))

g2 = StateGraph(State)
g2.add_node("a", a)
g2.add_node("reset", reset)
g2.add_edge(START, "a")
g2.add_edge("a", "reset")
g2.add_edge("reset", END)
app2 = g2.compile()
print(app2.invoke({"last": "", "logs": ["start"], "best": 0}))
