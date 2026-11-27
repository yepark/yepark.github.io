from langchain.agents import create_agent
from langchain.agents.middleware import (
    before_model, wrap_tool_call, ModelCallLimitMiddleware)
from langchain.tools import tool
from lc_mlx import ChatMLX

@tool
def multiply(a: int, b: int) -> int:
    """두 정수의 곱을 정확하게 계산한다."""
    return a * b

@before_model
def log_model(state, runtime):
    print(f"[before_model] 메시지 {len(state['messages'])}개")

@wrap_tool_call
def log_tool(request, handler):
    call = request.tool_call
    print(f"[tool] {call['name']}({call['args']})")
    result = handler(request)          # 실제 도구 실행
    print(f"[tool] 결과 {result.content}")
    return result

llm = ChatMLX(model_id="mlx-community/Qwen2.5-3B-Instruct-4bit")
agent = create_agent(
    model=llm,
    tools=[multiply],
    system_prompt="곱셈은 multiply 도구로 계산하고 "
                  "한국어 한 문장으로 답하세요.",
    middleware=[log_model, log_tool,
                ModelCallLimitMiddleware(run_limit=5)],
)
print(type(agent).__name__)

result = agent.invoke({"messages": [
    {"role": "user", "content": "123과 456을 곱해 주세요."}]})
for m in result["messages"]:
    print(f"{m.type:5}", repr(m.content)[:40],
          getattr(m, "tool_calls", ""))
