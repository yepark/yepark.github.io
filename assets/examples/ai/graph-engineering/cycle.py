from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.errors import GraphRecursionError

MAX_REVISIONS = 2


class State(TypedDict):
    draft: str
    score: int
    revisions: int


def review(state: State):
    # 모델 대신 '글자 수'로 점수를 매긴다
    return {"score": len(state["draft"]) * 10}


def revise(state: State):
    return {"draft": state["draft"] + "+",
            "revisions": state["revisions"] + 1}


def route(state: State) -> Literal[
        "revise", "human", "__end__"]:
    if state["score"] >= 80:
        return END
    if state["revisions"] >= MAX_REVISIONS:
        return "human"
    return "revise"


def human(state: State):
    return {}


def build(router):
    b = StateGraph(State)
    b.add_node("review", review)
    b.add_node("revise", revise)
    b.add_node("human", human)
    b.add_edge(START, "review")
    b.add_conditional_edges("review", router)
    b.add_edge("revise", "review")
    b.add_edge("human", END)
    return b.compile()


def run(app, draft, **config):
    s = {"draft": draft, "score": 0, "revisions": 0}
    steps = []
    for up in app.stream(s, config,
                         stream_mode="updates"):
        steps.extend(up)
    print(draft, "->", " > ".join(steps))


guarded = build(route)
run(guarded, "초안입니다요")   # 6글자
run(guarded, "짧음")          # 2글자


def no_guard(state: State) -> Literal[
        "revise", "__end__"]:
    return END if state["score"] >= 800 else "revise"


loop = build(no_guard)
try:
    run(loop, "짧음", recursion_limit=6)
except GraphRecursionError as e:
    print(type(e).__name__)
    print(str(e).splitlines()[0])
print(guarded.get_graph().draw_mermaid())
