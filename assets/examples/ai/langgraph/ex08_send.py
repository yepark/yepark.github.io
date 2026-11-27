import operator
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send


class Overall(TypedDict):
    docs: list[str]
    summaries: Annotated[list[str], operator.add]
    report: str


class One(TypedDict):       # 일꾼 하나가 받는 상자
    doc: str


def fan_out(state: Overall):
    return [Send("summarize", {"doc": d})
            for d in state["docs"]]


def summarize(state: One):
    return {"summaries": [state["doc"][:3]]}


def combine(state: Overall):
    return {"report": " | ".join(state["summaries"])}


g = StateGraph(Overall)
g.add_node("summarize", summarize)
g.add_node("combine", combine)
g.add_conditional_edges(START, fan_out, ["summarize"])
g.add_edge("summarize", "combine")
g.add_edge("combine", END)
app = g.compile()

docs = ["사과는 빨갛다", "바나나는 노랗다", "포도는 보라색"]
for u in app.stream({"docs": docs},
                    stream_mode="updates"):
    print(u)
