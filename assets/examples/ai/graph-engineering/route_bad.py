from route import State, StateGraph, START, END
from route import classify, howto, billing, clarify


def raw_route(state: State):
    return state["category"]  # 검사 없이 그대로


b = StateGraph(State)
b.add_node("classify", classify)
b.add_node("howto", howto)
b.add_node("billing", billing)
b.add_node("clarify", clarify)
b.add_edge(START, "classify")
b.add_conditional_edges("classify", raw_route)
for n in ("howto", "billing", "clarify"):
    b.add_edge(n, END)
app = b.compile()

try:
    print(app.invoke({"text": "안녕"}))
except Exception as e:
    print(type(e).__name__, ":", e)
