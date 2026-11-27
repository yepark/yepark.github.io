from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


class In(TypedDict):
    question: str


class Out(TypedDict):
    answer: str


class Overall(In, Out):
    draft: str          # 안에서만 쓰는 메모


class Secret(TypedDict):
    hint: str           # 두 노드 사이 비밀 쪽지


def plan(state: In) -> Secret:
    return {"hint": state["question"].upper()}


def write(state: Secret) -> dict:
    return {"draft": f"[{state['hint']}]"}


def finish(state: Overall) -> Out:
    return {"answer": state["draft"] + " 끝"}


g = StateGraph(Overall, input_schema=In,
               output_schema=Out)
g.add_node("plan", plan)
g.add_node("write", write)
g.add_node("finish", finish)
g.add_edge(START, "plan")
g.add_edge("plan", "write")
g.add_edge("write", "finish")
g.add_edge("finish", END)
app = g.compile()

print(app.invoke({"question": "hi"}))
for u in app.stream({"question": "hi"},
                    stream_mode="updates"):
    print(u)
