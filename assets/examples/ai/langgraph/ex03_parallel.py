import operator
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


class NoReducer(TypedDict):
    found: list[str]


class WithReducer(TypedDict):
    found: Annotated[list[str], operator.add]


def build(schema):
    g = StateGraph(schema)
    g.add_node("web", lambda s: {"found": ["웹"]})
    g.add_node("docs", lambda s: {"found": ["문서"]})
    g.add_edge(START, "web")   # START에서 두 갈래
    g.add_edge(START, "docs")
    g.add_edge("web", END)
    g.add_edge("docs", END)
    return g.compile()


try:
    build(NoReducer).invoke({"found": []})
except Exception as e:
    print(type(e).__name__)
    print(str(e).splitlines()[0])

print(build(WithReducer).invoke({"found": []}))
