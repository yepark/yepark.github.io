from typing import Literal
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict, total=False):
    query: str
    docs: list[str]
    status: Literal["ok", "empty", "timeout"]
    answer: str


def fake_search(q: str) -> list[str]:
    if q == "느린 질문":
        raise TimeoutError
    return ["문서1"] if "내보내기" in q else []


def search(s: State):
    try:
        docs = fake_search(s["query"])
    except TimeoutError:
        return {"docs": [], "status": "timeout"}
    return {"docs": docs,
            "status": "ok" if docs else "empty"}


def route(s: State) -> Literal[
        "write", "no_evidence", "retry_later"]:
    return {"ok": "write",
            "empty": "no_evidence",
            "timeout": "retry_later"}[s["status"]]


def write(s: State):
    return {"answer": f"근거 {s['docs']}로 답변"}


def no_evidence(s: State):
    return {"answer": "찾은 근거가 없어 답할 수 없음"}


def retry_later(s: State):
    return {"answer": "검색 장애: 잠시 뒤 다시 시도"}


b = StateGraph(State)
for f in (search, write, no_evidence, retry_later):
    b.add_node(f.__name__, f)
b.add_edge(START, "search")
b.add_conditional_edges("search", route)
for n in ("write", "no_evidence", "retry_later"):
    b.add_edge(n, END)
app = b.compile()

for q in ["내보내기 되나요", "날씨 어때", "느린 질문"]:
    r = app.invoke({"query": q})
    print(f"{q:10} {r['status']:8} {r['answer']}")
