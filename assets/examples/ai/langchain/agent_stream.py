from langchain.agents import create_agent
from langchain.agents.middleware import ModelCallLimitMiddleware
from langchain.tools import tool
from lc_mlx import ChatMLX

@tool
def multiply(a: int, b: int) -> int:
    """두 정수의 곱을 정확하게 계산한다."""
    return a * b

llm = ChatMLX(model_id="mlx-community/Qwen2.5-3B-Instruct-4bit")
agent = create_agent(llm, tools=[multiply])
print(list(agent.get_graph().nodes))

q = {"messages": [{"role": "user",
                   "content": "12와 34를 곱해 주세요."}]}
for step in agent.stream(q, stream_mode="updates"):
    for node, update in step.items():
        m = update["messages"][-1]
        print(node, "->", m.type, repr(m.content)[:30])

limited = create_agent(llm, tools=[multiply], middleware=[
    ModelCallLimitMiddleware(run_limit=1)])
r = limited.invoke(q)
print(r["messages"][-1].type, r["messages"][-1].content)
