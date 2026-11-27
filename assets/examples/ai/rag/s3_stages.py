from langchain_core.output_parsers import StrOutputParser
from store import store
from prompt import prompt, format_docs
from llm import model, MODEL_ID

retriever = store.as_retriever(search_kwargs={"k": 2})
q = "결제하고 10일 지났는데 환불되나요?"

docs = retriever.invoke(q)                 # 1. 검색
print("① 검색:", [d.metadata["source"] for d in docs])

value = prompt.invoke({                    # 2. 프롬프트
    "context": format_docs(docs),
    "question": q,
})
print("② 프롬프트:")
for m in value.to_messages():
    print(f"  {m.type}: {m.content}")

msg = model.invoke(value)                  # 3. 모델
print("③ 모델 결과 타입:", type(msg).__name__)
print("   content:", repr(msg.content))

text = StrOutputParser().invoke(msg)       # 4. 파서
print("④ 파서 결과는 str인가?", isinstance(text, str))
print("   ", text)
print("모델:", MODEL_ID)
