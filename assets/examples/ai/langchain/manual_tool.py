from langchain.tools import tool
from langchain.messages import HumanMessage
from lc_mlx import ChatMLX

@tool
def multiply(a: int, b: int) -> int:
    """두 정수의 곱을 정확하게 계산한다."""
    return a * b

print(multiply.name)
print(multiply.description)
print(multiply.args)

llm = ChatMLX(model_id="mlx-community/Qwen2.5-3B-Instruct-4bit")
llm_t = llm.bind_tools([multiply])
msgs = [HumanMessage("123과 456을 곱해 주세요.")]
ai = llm_t.invoke(msgs)
print("content:", repr(ai.content))
print("tool_calls:", ai.tool_calls)
msgs.append(ai)
for call in ai.tool_calls:
    tm = multiply.invoke(call)
    print(type(tm).__name__, tm.content, tm.tool_call_id == call["id"])
    msgs.append(tm)
final = llm_t.invoke(msgs)
print("final:", final.content)
