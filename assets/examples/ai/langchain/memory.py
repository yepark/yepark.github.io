from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver
from lc_mlx import ChatMLX

llm = ChatMLX(model_id="mlx-community/Qwen2.5-3B-Instruct-4bit")
agent = create_agent(
    llm, tools=[], checkpointer=InMemorySaver(),
    system_prompt="반드시 한국어로 답하세요. "
                  "모르는 것은 모른다고 답하세요.")

def ask(text, thread):
    cfg = {"configurable": {"thread_id": thread}}
    r = agent.invoke(
        {"messages": [{"role": "user", "content": text}]},
        cfg)
    return r["messages"]

ask("제 이름은 예진입니다.", "A")
m = ask("제 이름이 뭐였죠?", "A")
print("A:", m[-1].content, f"(메시지 {len(m)}개)")
m = ask("제 이름이 뭐였죠?", "B")
print("B:", m[-1].content, f"(메시지 {len(m)}개)")
