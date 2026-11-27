from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langgraph.graph import MessagesState, StateGraph
from langgraph.graph import START, END
from langgraph.prebuilt import ToolNode


@tool
def divide(a: int, b: int) -> float:
    """a를 b로 나눈다."""
    return a / b


def run(calls, **kw):
    g = StateGraph(MessagesState)
    g.add_node("tools", ToolNode([divide], **kw))
    g.add_edge(START, "tools")
    g.add_edge("tools", END)
    msg = AIMessage("", tool_calls=calls)
    out = g.compile().invoke({"messages": [msg]})
    for m in out["messages"][1:]:
        print(" ", m.tool_call_id, m.status,
              m.content[:50])


def call(i, **args):
    return {"name": "divide", "args": args, "id": i}


print("1) 정상 두 개를 한 번에")
run([call("c1", a=6, b=3), call("c2", a=9, b=3)])
print("2) 인자 형식이 틀림 (기본 설정)")
run([call("c3", a="여섯", b=3)])
print("3) 0으로 나눔 (기본 설정)")
try:
    run([call("c4", a=1, b=0)])
except ZeroDivisionError as e:
    print("  예외가 그대로 올라옴:", e)
print("4) handle_tool_errors=True")
run([call("c5", a=1, b=0)], handle_tool_errors=True)
