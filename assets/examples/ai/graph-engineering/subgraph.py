from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


# 하위 그래프: 자기만의 상태 계약
class CheckState(TypedDict, total=False):
    draft: str
    problems: list[str]


def find_problems(s: CheckState):
    bad = [w for w in ("아마", "보통") if w in s["draft"]]
    return {"problems": bad}


sb = StateGraph(CheckState)
sb.add_node("find_problems", find_problems)
sb.add_edge(START, "find_problems")
sb.add_edge("find_problems", END)
checker = sb.compile()


# 상위 그래프: 상태 키가 다르다
class Parent(TypedDict, total=False):
    answer: str
    passed: bool


def check(s: Parent):
    out = checker.invoke({"draft": s["answer"]})
    return {"passed": not out["problems"]}


pb = StateGraph(Parent)
pb.add_node("check", check)
pb.add_edge(START, "check")
pb.add_edge("check", END)
app = pb.compile()

for a in ["관리자만 가능합니다", "아마 될 거예요"]:
    print(a, "->", app.invoke({"answer": a}))

for ns, up in app.stream({"answer": "보통 됩니다"},
                         stream_mode="updates",
                         subgraphs=True):
    print(ns, up)
