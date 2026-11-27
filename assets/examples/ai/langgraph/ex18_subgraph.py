from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END


# 1) 부모와 같은 키(text)를 쓰는 서브그래프
class Shared(TypedDict, total=False):
    text: str
    sub_note: str          # 서브그래프 안에서만 쓰는 키


def clean(s: Shared):
    return {"text": s["text"].strip(), "sub_note": "ok"}


def shout(s: Shared):
    return {"text": s["text"].upper()}


sb = StateGraph(Shared)
sb.add_node("clean", clean)
sb.add_node("shout", shout)
sb.add_edge(START, "clean")
sb.add_edge("clean", "shout")
sb.add_edge("shout", END)
sub = sb.compile()


class Parent(TypedDict):
    text: str


pb = StateGraph(Parent)
pb.add_node("prep", sub)        # 컴파일된 그래프 = 노드
pb.add_node("done", lambda s: {"text": s["text"] + "!"})
pb.add_edge(START, "prep")
pb.add_edge("prep", "done")
pb.add_edge("done", END)
parent = pb.compile()
print(parent.invoke({"text": "  hi  "}))

for ns, upd in parent.stream({"text": " hi "},
                             stream_mode="updates",
                             subgraphs=True):
    print(ns, upd)


# 2) 키가 다르면 노드 함수 안에서 바꿔 끼운다
class Order(TypedDict):
    order_text: str
    shipped: str


def call_sub(s: Order):
    out = sub.invoke({"text": s["order_text"]})
    return {"shipped": out["text"]}


ob = StateGraph(Order)
ob.add_node("call_sub", call_sub)
ob.add_edge(START, "call_sub")
ob.add_edge("call_sub", END)
print(ob.compile().invoke({"order_text": " book "}))
