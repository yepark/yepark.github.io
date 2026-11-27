from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict, total=False):
    text: str
    category: str
    answer: str


def classify(state: State):
    t = state["text"].strip()
    if not t:
        return {"category": "empty"}
    if "결제" in t or "환불" in t:
        return {"category": "billing"}
    if "어떻게" in t:
        return {"category": "howto"}
    return {"category": "unknown"}


Route = Literal["howto", "billing", "clarify"]


def route(state: State) -> Route:
    c = state["category"]
    if c in ("howto", "billing"):
        return c
    return "clarify"  # 모르는 값은 모두 여기로


def howto(state: State):
    return {"answer": "문서 검색 경로"}


def billing(state: State):
    return {"answer": "결제 담당자 경로"}


def clarify(state: State):
    return {"answer": "질문을 조금 더 알려 주세요"}


b = StateGraph(State)
b.add_node("classify", classify)
b.add_node("howto", howto)
b.add_node("billing", billing)
b.add_node("clarify", clarify)
b.add_edge(START, "classify")
b.add_conditional_edges("classify", route)
for n in ("howto", "billing", "clarify"):
    b.add_edge(n, END)
app = b.compile()

if __name__ == "__main__":
    for q in ["비밀번호 어떻게 바꿔요?",
              "결제가 두 번 됐어요",
              "   ",
              "안녕"]:
        r = app.invoke({"text": q})
        print(repr(q), "->", r["category"], "|", r["answer"])
    print(app.get_graph().draw_mermaid())
