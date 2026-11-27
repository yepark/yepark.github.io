import operator
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    log: Annotated[list[str], operator.add]


def node(name):
    def fn(state: State):
        return {"log": [name]}
    return fn


def build(wait_all: bool):
    b = StateGraph(State)
    for n in ("a", "a2", "b", "join"):
        b.add_node(n, node(n))
    b.add_edge(START, "a")
    b.add_edge(START, "b")
    b.add_edge("a", "a2")   # a 쪽이 한 단계 더 길다
    if wait_all:
        b.add_edge(["a2", "b"], "join")
    else:
        b.add_edge("a2", "join")
        b.add_edge("b", "join")
    b.add_edge("join", END)
    return b.compile()


for wait_all in (False, True):
    out = build(wait_all).invoke({"log": []})
    print(f"wait_all={wait_all}:", out["log"])
