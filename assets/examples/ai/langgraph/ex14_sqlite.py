import sys
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import MessagesState, StateGraph
from langgraph.graph import START, END


def echo(state: MessagesState):
    n = len(state["messages"])
    return {"messages": [("ai", f"지금까지 {n}개")]}


g = StateGraph(MessagesState)
g.add_node("echo", echo)
g.add_edge(START, "echo")
g.add_edge("echo", END)

with SqliteSaver.from_conn_string("chat.db") as saver:
    app = g.compile(checkpointer=saver)
    cfg = {"configurable": {"thread_id": "user-7"}}
    out = app.invoke(
        {"messages": [("user", sys.argv[1])]}, cfg)
    print(out["messages"][-1].content)
