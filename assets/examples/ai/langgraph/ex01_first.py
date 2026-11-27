from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


class TextState(TypedDict, total=False):
    original: str
    cleaned: str
    answer: str


def normalize(state: TextState):
    return {"cleaned": state["original"].strip()}


def choose_route(state: TextState):
    return "valid" if state["cleaned"] else "empty"


def write_answer(state: TextState):
    text = state["cleaned"]
    return {"answer": f"입력: {text} / 글자 수: {len(text)}"}


def explain_empty(state: TextState):
    return {"answer": "내용을 입력해 주세요."}


builder = StateGraph(TextState)
builder.add_node("normalize", normalize)
builder.add_node("write_answer", write_answer)
builder.add_node("explain_empty", explain_empty)

builder.add_edge(START, "normalize")
builder.add_conditional_edges(
    "normalize",
    choose_route,
    {"valid": "write_answer", "empty": "explain_empty"},
)
builder.add_edge("write_answer", END)
builder.add_edge("explain_empty", END)

app = builder.compile()

if __name__ == "__main__":
    for text in ["  안녕하세요  ", "   "]:
        print(app.invoke({"original": text}))
    print(app.get_graph().draw_mermaid())
