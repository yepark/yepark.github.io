from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command, interrupt


class S(TypedDict, total=False):
    email: str
    status: str


def draft(state: S):
    return {"email": "내일 회의는 10시입니다."}


def approve(state: S):
    print("  (approve 노드 시작)")
    answer = interrupt({"질문": "보낼까요?",
                        "초안": state["email"]})
    print("  (사람 답:", answer, ")")
    if answer["ok"]:
        return {"status": "sent"}
    return {"status": "rejected"}


g = StateGraph(S)
g.add_node("draft", draft)
g.add_node("approve", approve)
g.add_edge(START, "draft")
g.add_edge("draft", "approve")
g.add_edge("approve", END)
app = g.compile(checkpointer=InMemorySaver())

cfg = {"configurable": {"thread_id": "mail-1"}}
print("1) 첫 실행")
r = app.invoke({}, cfg)
print(r["__interrupt__"])
print("next:", app.get_state(cfg).next)

print("2) 재개")
r = app.invoke(Command(resume={"ok": True}), cfg)
print(r)

print("3) 체크포인터 없이")
plain = g.compile()
r = plain.invoke({})
print("멈춤 표시:", "__interrupt__" in r)
try:
    plain.invoke(Command(resume={"ok": True}))
except RuntimeError as e:
    print("RuntimeError:", e)
