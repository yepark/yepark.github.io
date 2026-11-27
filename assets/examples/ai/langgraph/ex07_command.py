import operator
from typing import Annotated, Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command


class State(TypedDict):
    amount: int
    path: Annotated[list[str], operator.add]


def review(state: State) -> Command[
        Literal["auto_ok", "manager"]]:
    big = state["amount"] >= 100
    return Command(
        update={"path": ["review"]},
        goto="manager" if big else "auto_ok",
    )


def auto_ok(state: State):
    return {"path": ["auto_ok"]}


def manager(state: State):
    return {"path": ["manager"]}


g = StateGraph(State)
g.add_node("review", review)
g.add_node("auto_ok", auto_ok)
g.add_node("manager", manager)
g.add_edge(START, "review")
g.add_edge("auto_ok", END)
g.add_edge("manager", END)
app = g.compile()
for n in [30, 250]:
    r = app.invoke({"amount": n, "path": []})
    print(n, r["path"])

# 함정: Command와 일반 엣지를 같은 노드에 섞기
g.add_edge("review", "auto_ok")
bad = g.compile()
print("섞음", bad.invoke({"amount": 250, "path": []})["path"])
print(app.get_graph().draw_mermaid())
