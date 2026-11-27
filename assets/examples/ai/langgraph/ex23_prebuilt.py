import warnings
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent
from ex10_agent import FakeToolModel, multiply


def fake():
    return FakeToolModel(messages=iter([
        AIMessage("", tool_calls=[{
            "name": "multiply", "args": {"a": 3, "b": 4},
            "id": "c1"}]),
        AIMessage("3 곱하기 4는 12입니다.")]))


with warnings.catch_warnings(record=True) as w:
    warnings.simplefilter("always")
    create_react_agent(fake(), [multiply])
    print(w[0].category.__name__)
    print(str(w[0].message))

agent = create_agent(fake(), tools=[multiply])
print(type(agent).__name__)
print(list(agent.get_graph().nodes))
out = agent.invoke(
    {"messages": [("user", "3 곱하기 4?")]})
print(out["messages"][-1].content)
