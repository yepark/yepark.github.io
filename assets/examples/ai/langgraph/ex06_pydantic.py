from dataclasses import dataclass, field
from pydantic import BaseModel
from langgraph.graph import StateGraph, START, END


class Order(BaseModel):
    item: str
    qty: int


def check(state: Order):
    print("노드 안 타입:", type(state).__name__,
          state.qty)
    return {"qty": state.qty + 1}


g = StateGraph(Order)
g.add_node("check", check)
g.add_edge(START, "check")
g.add_edge("check", END)
app = g.compile()

print(app.invoke({"item": "펜", "qty": "2"}))
try:
    app.invoke({"item": "펜", "qty": "두 개"})
except Exception as e:
    print(type(e).__name__)
    print(str(e).splitlines()[0])


@dataclass
class Cart:
    items: list[str] = field(default_factory=list)
    note: str = "없음"


def add(state: Cart):
    print("note =", state.note)
    return {"items": state.items + ["사과"]}


g2 = StateGraph(Cart)
g2.add_node("add", add)
g2.add_edge(START, "add")
g2.add_edge("add", END)
print(g2.compile().invoke({}))
