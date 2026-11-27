from lc_mlx import ChatMLX
llm = ChatMLX(model_id="mlx-community/Qwen2.5-3B-Instruct-4bit")
r = llm.invoke([("system", "한국어로 한 문장으로 답하세요."),
                ("human", "Python 리스트는 무엇인가요?")])
print(type(r).__name__)
print(r.content)
print(r.usage_metadata)
