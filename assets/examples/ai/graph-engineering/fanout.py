import operator
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

DOCS = {"manual": "내보내기 메뉴",
        "policy": "관리자만 가능",
        "faq": "무료 플랜 제한"}


class State(TypedDict):
    question: str
    sources: list[str]
    found: Annotated[list[str], operator.add]
    answer: str


class Job(TypedDict):
    question: str
    source: str


def plan(state: State):
    return {"sources": ["manual", "policy", "faq"]}


def fan_out(state: State):
    return [Send("search", {"question": state["question"],
                            "source": s})
            for s in state["sources"]]


def search(job: Job):
    return {"found": [f"{job['source']}: "
                      f"{DOCS[job['source']]}"]}


def write(state: State):
    return {"answer": " / ".join(sorted(state["found"]))}


b = StateGraph(State)
b.add_node("plan", plan)
b.add_node("search", search)
b.add_node("write", write)
b.add_edge(START, "plan")
b.add_conditional_edges("plan", fan_out, ["search"])
b.add_edge("search", "write")
b.add_edge("write", END)
app = b.compile()

init = {"question": "내보내기 되나요?", "sources": [],
        "found": [], "answer": ""}
for up in app.stream(init, stream_mode="updates"):
    print(up)
print(app.get_graph().draw_mermaid())
