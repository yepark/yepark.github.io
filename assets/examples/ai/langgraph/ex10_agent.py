from langchain_core.language_models.fake_chat_models \
    import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import tool
from langgraph.graph import MessagesState, StateGraph
from langgraph.graph import START
from langgraph.prebuilt import ToolNode, tools_condition


@tool
def multiply(a: int, b: int) -> int:
    """두 정수를 곱한다."""
    return a * b


class FakeToolModel(GenericFakeChatModel):
    def bind_tools(self, tools, **kwargs):
        return self   # 정해 둔 답만 내므로 도구 정보는 무시


# 모델이 낼 답을 순서대로 정해 둔다
script = iter([
    AIMessage("", tool_calls=[{
        "name": "multiply", "args": {"a": 12, "b": 7},
        "id": "call_1"}]),
    AIMessage("12 곱하기 7은 84입니다."),
])
model = FakeToolModel(messages=script)
model = model.bind_tools([multiply])


def agent(state: MessagesState):
    return {"messages": [model.invoke(state["messages"])]}


g = StateGraph(MessagesState)
g.add_node("agent", agent)
g.add_node("tools", ToolNode([multiply]))
g.add_edge(START, "agent")
g.add_conditional_edges("agent", tools_condition)
g.add_edge("tools", "agent")
app = g.compile()

if __name__ == "__main__":
    q = {"messages": [("user", "12 곱하기 7은?")]}
    for u in app.stream(q, stream_mode="updates"):
        for node, upd in u.items():
            m = upd["messages"][-1]
            print(f"[{node}] {type(m).__name__}:",
                  m.content or m.tool_calls)
    print(app.get_graph().draw_mermaid())
