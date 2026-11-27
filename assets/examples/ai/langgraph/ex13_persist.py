import operator
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver


class S(TypedDict, total=False):
    topic: str
    joke: str
    log: Annotated[list[str], operator.add]


def pick(state: S):
    return {"topic": "양말", "log": ["pick"]}


def write(state: S):
    return {"joke": f"{state['topic']}이 사라졌다",
            "log": ["write"]}


g = StateGraph(S)
g.add_node("pick", pick)
g.add_node("write", write)
g.add_edge(START, "pick")
g.add_edge("pick", "write")
g.add_edge("write", END)
app = g.compile(checkpointer=InMemorySaver())

cfg = {"configurable": {"thread_id": "t1"}}
print(app.invoke({"log": []}, cfg))

snap = app.get_state(cfg)
print("next:", snap.next)
print("step:", snap.metadata["step"])

print("--- history (최신부터)")
hist = list(app.get_state_history(cfg))
for h in hist:
    print(h.metadata["step"], h.next,
          h.metadata["source"], h.values.get("topic"))

before = next(h for h in hist if h.next == ("write",))
print("--- replay")
print(app.invoke(None, before.config))
print("--- fork")
fork = app.update_state(before.config,
                        {"topic": "우산"})
print(app.invoke(None, fork))
print("기록 수:", len(list(app.get_state_history(cfg))))
print("다른 thread:", app.get_state(
    {"configurable": {"thread_id": "t2"}}).values)
for h in app.get_state_history(cfg):
    print(h.metadata["step"], h.next,
          h.metadata["source"], h.values.get("joke"))
