from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver


class S(TypedDict):
    x: int


g = StateGraph(S)
g.add_node("a", lambda s: {"x": s["x"] + 1})
g.add_node("b", lambda s: {"x": s["x"] * 10})
g.add_edge(START, "a")
g.add_edge("a", "b")
g.add_edge("b", END)
app = g.compile(checkpointer=InMemorySaver(),
                interrupt_before=["b"])

cfg = {"configurable": {"thread_id": "dbg"}}
print(app.invoke({"x": 1}, cfg))
print("next:", app.get_state(cfg).next)
app.update_state(cfg, {"x": 5})   # 값을 고쳐 보고
print(app.invoke(None, cfg))      # None으로 이어 가기
