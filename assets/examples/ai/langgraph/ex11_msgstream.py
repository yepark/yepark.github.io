from langchain_core.language_models.fake_chat_models \
    import GenericFakeChatModel
from langgraph.graph import MessagesState, StateGraph
from langgraph.graph import START, END

model = GenericFakeChatModel(
    messages=iter(["LangGraph는 상태 그래프입니다"]))


def chat(state: MessagesState):
    return {"messages": [model.invoke(state["messages"])]}


g = StateGraph(MessagesState)
g.add_node("chat", chat)
g.add_edge(START, "chat")
g.add_edge("chat", END)
app = g.compile()

for chunk, meta in app.stream(
        {"messages": [("user", "한 줄 설명")]},
        stream_mode="messages"):
    print(repr(chunk.content), meta["langgraph_node"])
