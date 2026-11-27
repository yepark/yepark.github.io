from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command

saver = InMemorySaver()   # v1, v2가 같은 저장소를 쓴다
cfg = {"configurable": {"thread_id": "old-1"}}


class State(TypedDict, total=False):
    decision: str


def ask(state: State):
    return {"decision": interrupt("승인할까요?")}


def build(name: str):
    b = StateGraph(State)
    b.add_node(name, ask)
    b.add_edge(START, name)
    b.add_edge(name, END)
    return b.compile(checkpointer=saver)


v1 = build("approve")
v1.invoke({}, cfg)
print("v1 멈춤, next:", v1.get_state(cfg).next)

v2 = build("human_approval")   # 노드 이름만 바꿈
print("v2가 본 next:", v2.get_state(cfg).next)
out = v2.invoke(Command(resume="approved"), cfg)
print("v2 재개 결과:", out)
