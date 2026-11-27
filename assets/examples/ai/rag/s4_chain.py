from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from store import store
from prompt import prompt, format_docs
from llm import model

retriever = store.as_retriever(search_kwargs={"k": 2})

chain = (
    {
        "context": retriever | format_docs,
        "question": RunnablePassthrough(),
    }
    | prompt
    | model
    | StrOutputParser()
)

for q in [
    "프로 플랜은 한 달에 얼마예요?",
    "토요일에 전화 상담 되나요?",
    "회사 대표 이름이 뭐예요?",
]:
    print("Q:", q)
    print("A:", chain.invoke(q))
